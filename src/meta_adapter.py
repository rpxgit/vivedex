import os
import json
import base64
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.schemas import ModelIdentificationResult, CandidateIdentification


class MetaAPIConfigurationError(RuntimeError):
    """Raised when the required Meta API credentials are not configured."""
    pass


class MetaAPIRequestError(RuntimeError):
    """Raised when the Meta Model API request fails."""
    pass


class MetaAPIAdapter:
    """
    Adapter for the Meta Model API using the verified endpoint and model identifier.
    
    Verified parameters:
      Base URL: https://api.meta.ai/v1
      Endpoint: /chat/completions
      Model: muse-spark-1.3
      Auth: Authorization: Bearer $MODEL_API_KEY
    """

    BASE_URL = "https://api.meta.ai/v1"
    ENDPOINT = f"{BASE_URL}/chat/completions"
    MODEL_ID = "muse-spark-1.3"

    SYSTEM_PROMPT = (
        "You are an expert scientific organism identification assistant for the Vivédex biodiversity platform. "
        "Analyze the provided image of an organism and return a strictly structured JSON response. "
        "Do NOT invent numerical probabilities or percentages for the identification. "
        "Every identification is a candidate suggestion and must be treated as such. "
        "Output ONLY a single JSON object with the following schema:\n"
        "{\n"
        '  "model": "muse-spark-1.3",\n'
        '  "observation_summary": "Short natural language description of visible subject and context",\n'
        '  "candidates": [\n'
        "    {\n"
        '      "common_name": "Vernacular name or null",\n'
        '      "scientific_name": "Binomial/trinomial or null",\n'
        '      "suggested_rank": "SPECIES, GENUS, FAMILY, etc.",\n'
        '      "visual_evidence": ["Key visible trait 1", "Key visible trait 2"],\n'
        '      "lookalikes": ["Lookalike taxon 1", "Lookalike taxon 2"],\n'
        '      "uncertainty_note": "Explanation of potential confusion or limitations"\n'
        "    }\n"
        "  ],\n"
        '  "limitations": "The result is an AI-generated candidate suggestion, not an authoritative or expert-confirmed identification."\n'
        "}"
    )

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MODEL_API_KEY") or os.getenv("META_API_KEY")

    def _require_api_key(self) -> str:
        if not self.api_key:
            raise MetaAPIConfigurationError(
                "Meta API key is missing. Set the 'MODEL_API_KEY' environment variable. "
                "Live API calls cannot be made without a valid key."
            )
        return self.api_key

    def identify_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> ModelIdentificationResult:
        """
        Send image to Meta Model API and parse response into ModelIdentificationResult.
        
        Args:
            image_bytes: Raw cleaned image bytes
            mime_type: MIME type of the image (e.g. image/jpeg, image/png)
            
        Returns:
            ModelIdentificationResult parsed and validated
            
        Raises:
            MetaAPIConfigurationError: if MODEL_API_KEY is missing
            MetaAPIRequestError: if the API request fails or returns invalid response
        """
        api_key = self._require_api_key()

        # Format image as Base64 data URL
        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64_img}"

        payload = {
            "model": self.MODEL_ID,
            "messages": [
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Identify the organism visible in this photograph. Return strict JSON following the specified schema."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.2
        }

        req_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Vivedex-MVP/0.1.0"
        }

        req = urllib.request.Request(self.ENDPOINT, data=req_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                status_code = resp.status
                resp_bytes = resp.read()
        except urllib.error.HTTPError as e:
            # Sanitize error body: extract structured error message if JSON, avoid echoing request headers/tokens
            safe_msg = f"HTTP {e.code}"
            try:
                err_body = e.read().decode("utf-8", errors="replace")
                parsed_err = json.loads(err_body)
                if isinstance(parsed_err, dict) and "error" in parsed_err:
                    err_info = parsed_err["error"]
                    if isinstance(err_info, dict) and "message" in err_info:
                        safe_msg += f": {err_info['message']}"
                    elif isinstance(err_info, str):
                        safe_msg += f": {err_info}"
            except Exception:
                pass
            raise MetaAPIRequestError(f"Meta Model API request failed ({safe_msg})") from e
        except urllib.error.URLError as e:
            raise MetaAPIRequestError(f"Failed to connect to Meta Model API: {str(e.reason)}") from e
        except Exception as e:
            raise MetaAPIRequestError(f"Unexpected error communicating with Meta Model API: {type(e).__name__}") from e

        try:
            raw_json = json.loads(resp_bytes.decode("utf-8"))
            content_str = raw_json["choices"][0]["message"]["content"]
            # In case the model wrapped JSON in markdown code fences
            cleaned_str = content_str.strip()
            if cleaned_str.startswith("```json"):
                cleaned_str = cleaned_str[7:]
            elif cleaned_str.startswith("```"):
                cleaned_str = cleaned_str[3:]
            if cleaned_str.endswith("```"):
                cleaned_str = cleaned_str[:-3]
            
            model_data = json.loads(cleaned_str.strip())
            return ModelIdentificationResult.model_validate(model_data)
        except Exception as e:
            raise MetaAPIRequestError(f"Failed to parse model response into valid schema: {str(e)}") from e

