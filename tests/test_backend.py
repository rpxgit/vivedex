import io
import json
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image

from src.image_processor import (
    validate_image,
    preprocess_image,
    ImageValidationError,
    MAX_IMAGE_SIZE_BYTES,
)
from src.schemas import (
    CandidateIdentification,
    ModelIdentificationResult,
    GBIFMatchResult,
    VivedexResult,
)
from src.meta_adapter import (
    MetaAPIAdapter,
    MetaAPIConfigurationError,
    MetaAPIRequestError,
)
from src.gbif_adapter import GBIFAdapter, GBIFRequestError
from src.backend import VivedexBackend


def create_test_image(format="JPEG", size=(100, 100), color="blue"):
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


class TestImageProcessor(unittest.TestCase):
    def test_valid_jpeg(self):
        img_bytes = create_test_image("JPEG")
        fmt = validate_image(img_bytes, "image/jpeg")
        self.assertEqual(fmt, "JPEG")

    def test_valid_png(self):
        img_bytes = create_test_image("PNG")
        fmt = validate_image(img_bytes, "image/png")
        self.assertEqual(fmt, "PNG")

    def test_valid_webp(self):
        img_bytes = create_test_image("WEBP")
        fmt = validate_image(img_bytes, "image/webp")
        self.assertEqual(fmt, "WEBP")

    def test_unsupported_mime(self):
        img_bytes = create_test_image("JPEG")
        with self.assertRaises(ImageValidationError) as ctx:
            validate_image(img_bytes, "image/gif")
        self.assertIn("Unsupported image type", str(ctx.exception))

    def test_empty_bytes(self):
        with self.assertRaises(ImageValidationError) as ctx:
            validate_image(b"", "image/jpeg")
        self.assertIn("empty", str(ctx.exception))

    def test_size_exceeded(self):
        fake_large = b"0" * (MAX_IMAGE_SIZE_BYTES + 1)
        with self.assertRaises(ImageValidationError) as ctx:
            validate_image(fake_large, "image/jpeg")
        self.assertIn("exceeds 8 MB limit", str(ctx.exception))

    def test_corrupted_bytes(self):
        corrupted = b"NOT_AN_IMAGE_HEADER_12345"
        with self.assertRaises(ImageValidationError) as ctx:
            validate_image(corrupted, "image/jpeg")
        self.assertIn("corrupted", str(ctx.exception).lower())

    def test_preprocess_strips_metadata(self):
        img_bytes = create_test_image("JPEG")
        clean_bytes, mime = preprocess_image(img_bytes)
        self.assertEqual(mime, "image/jpeg")
        self.assertGreater(len(clean_bytes), 0)
        # Verify clean bytes can still be opened as a valid image
        with Image.open(io.BytesIO(clean_bytes)) as img:
            self.assertEqual(img.format, "JPEG")


class TestSchemas(unittest.TestCase):
    def test_model_result_schema(self):
        data = {
            "model": "muse-spark-1.3",
            "observation_summary": "Small passerine bird on branch",
            "candidates": [
                {
                    "common_name": "House Sparrow",
                    "scientific_name": "Passer domesticus",
                    "suggested_rank": "SPECIES",
                    "visual_evidence": ["Black bib", "Conical beak"],
                    "lookalikes": ["Passer montanus"],
                    "uncertainty_note": "Clear plumage"
                }
            ],
            "limitations": "Candidate only"
        }
        res = ModelIdentificationResult.model_validate(data)
        self.assertEqual(res.model, "muse-spark-1.3")
        self.assertEqual(len(res.candidates), 1)
        self.assertEqual(res.candidates[0].scientific_name, "Passer domesticus")

    def test_gbif_schema_and_vivedex_consolidation(self):
        model_res = ModelIdentificationResult(
            observation_summary="Bird observation",
            candidates=[
                CandidateIdentification(
                    common_name="House Sparrow",
                    scientific_name="Passer domesticus",
                    visual_evidence=["Black bib"]
                )
            ]
        )
        gbif_res = GBIFMatchResult(
            query_name="Passer domesticus",
            matched_scientific_name="Passer domesticus (Linnaeus, 1758)",
            canonical_name="Passer domesticus",
            rank="SPECIES",
            status="ACCEPTED",
            match_type="EXACT",
            gbif_match_score=99,
            usage_key=5231190,
            retrieved_at="2026-11-04T17:20:01Z"
        )
        consolidated = VivedexResult(
            timestamp="2026-11-04T17:20:01Z",
            ai_candidate=model_res,
            taxonomic_resolution=gbif_res
        )

        json_str = consolidated.to_json()
        self.assertIn("Passer domesticus (Linnaeus, 1758)", json_str)
        self.assertIn("muse-spark-1.3", json_str)
        # Check that original proposed name is separate from matched name
        parsed = json.loads(json_str)
        self.assertEqual(
            parsed["ai_candidate"]["candidates"][0]["scientific_name"],
            "Passer domesticus"
        )
        self.assertEqual(
            parsed["taxonomic_resolution"]["matched_scientific_name"],
            "Passer domesticus (Linnaeus, 1758)"
        )


class TestMetaAPIAdapter(unittest.TestCase):
    def test_missing_api_key_raises_configuration_error(self):
        adapter = MetaAPIAdapter(api_key=None)
        with patch.dict("os.environ", {}, clear=True):
            adapter.api_key = None
            with self.assertRaises(MetaAPIConfigurationError) as ctx:
                adapter.identify_image(b"fake_bytes")
            self.assertIn("MODEL_API_KEY", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_successful_meta_call(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "model": "muse-spark-1.3",
                            "observation_summary": "Perched sparrow",
                            "candidates": [
                                {
                                    "common_name": "House Sparrow",
                                    "scientific_name": "Passer domesticus",
                                    "suggested_rank": "SPECIES",
                                    "visual_evidence": ["Black bib", "Conical beak"],
                                    "lookalikes": ["Passer montanus"],
                                    "uncertainty_note": "Clear view"
                                }
                            ],
                            "limitations": "AI-generated candidate"
                        })
                    }
                }
            ]
        }
        mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        adapter = MetaAPIAdapter(api_key="test_key")
        result = adapter.identify_image(b"fake_bytes")
        self.assertEqual(result.model, "muse-spark-1.3")
        self.assertEqual(result.candidates[0].scientific_name, "Passer domesticus")

    @patch("urllib.request.urlopen")
    def test_meta_call_markdown_code_fence_cleaning(self, mock_urlopen):
        raw_json_str = json.dumps({
            "model": "muse-spark-1.3",
            "observation_summary": "Sparrow",
            "candidates": [
                {
                    "scientific_name": "Passer domesticus"
                }
            ],
            "limitations": "Candidate"
        })
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [
                {
                    "message": {
                        "content": f"```json\n{raw_json_str}\n```"
                    }
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        adapter = MetaAPIAdapter(api_key="test_key")
        result = adapter.identify_image(b"fake_bytes")
        self.assertEqual(result.candidates[0].scientific_name, "Passer domesticus")


class TestGBIFAdapter(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_gbif_match_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_gbif_payload = {
            "usageKey": 5231190,
            "scientificName": "Passer domesticus (Linnaeus, 1758)",
            "canonicalName": "Passer domesticus",
            "rank": "SPECIES",
            "status": "ACCEPTED",
            "confidence": 99,
            "matchType": "EXACT",
            "kingdom": "Animalia",
            "phylum": "Chordata",
            "order": "Passeriformes",
            "family": "Passeridae",
            "genus": "Passer",
            "species": "Passer domesticus"
        }
        mock_resp.read.return_value = json.dumps(mock_gbif_payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        adapter = GBIFAdapter()
        res = adapter.match_species("Passer domesticus")
        self.assertEqual(res.match_type, "EXACT")
        self.assertEqual(res.canonical_name, "Passer domesticus")
        self.assertEqual(res.usage_key, 5231190)
        self.assertEqual(res.gbif_match_score, 99)
        self.assertEqual(res.source_url, "https://www.gbif.org/species/5231190")
        self.assertIn("Animalia", res.hierarchy["kingdom"])

    def test_gbif_empty_name(self):
        adapter = GBIFAdapter()
        res = adapter.match_species("")
        self.assertEqual(res.match_type, "NONE")


class TestVivedexBackend(unittest.TestCase):
    @patch("src.backend.preprocess_image")
    @patch("src.backend.validate_image")
    def test_full_pipeline_mocked(self, mock_val, mock_prep):
        mock_val.return_value = "JPEG"
        mock_prep.return_value = (b"clean_bytes", "image/jpeg")

        mock_meta = MagicMock()
        mock_meta.identify_image.return_value = ModelIdentificationResult(
            observation_summary="Bird observation",
            candidates=[
                CandidateIdentification(
                    common_name="House Sparrow",
                    scientific_name="Passer domesticus"
                )
            ]
        )

        mock_gbif = MagicMock()
        mock_gbif.match_species.return_value = GBIFMatchResult(
            query_name="Passer domesticus",
            matched_scientific_name="Passer domesticus (Linnaeus, 1758)",
            canonical_name="Passer domesticus",
            rank="SPECIES",
            status="ACCEPTED",
            match_type="EXACT",
            gbif_match_score=99,
            usage_key=5231190,
            retrieved_at="2026-11-04T17:20:01Z"
        )

        backend = VivedexBackend(meta_adapter=mock_meta, gbif_adapter=mock_gbif)
        res = backend.process_observation(b"raw_bytes", "image/jpeg")

        self.assertEqual(res.ai_candidate.candidates[0].scientific_name, "Passer domesticus")
        self.assertEqual(res.taxonomic_resolution.matched_scientific_name, "Passer domesticus (Linnaeus, 1758)")
        self.assertEqual(res.taxonomic_resolution.usage_key, 5231190)


if __name__ == "__main__":
    unittest.main()

