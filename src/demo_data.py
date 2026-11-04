"""Controlled demonstration data loader for Vivédex platform prototype.

Loads curated sample records clearly tagged with 'DEMO DATA' provenance.
Never stores plaintext passwords in source code.
"""

from __future__ import annotations

import json
import secrets
from typing import Any

from src.achievements import AchievementService
from src.auth import AuthService, generate_salt, hash_password
from src.database import Database, utc_now_iso

DEMO_PROVENANCE_TAG = "DEMO DATA"


def load_demo_dataset(db: Database) -> dict[str, Any]:
    """Load curated demonstration records into the database.

    All sample records are stamped with DEMO DATA provenance.
    Generates dynamic secure passwords at runtime.
    """
    now = utc_now_iso()
    auth_service = AuthService(db)
    achievement_service = AchievementService(db)

    # Generated runtime password (never hardcoded in source)
    runtime_demo_secret = secrets.token_urlsafe(12)
    salt_admin = generate_salt()
    hash_admin = hash_password(runtime_demo_secret, salt_admin)

    salt_curator = generate_salt()
    hash_curator = hash_password(runtime_demo_secret, salt_curator)

    with db.connect() as conn:
        cursor = conn.cursor()

        # 1. Create demo users if not present
        cursor.execute("SELECT id FROM users WHERE username = 'demo_admin';")
        admin_row = cursor.fetchone()
        if not admin_row:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, salt, role, is_active, created_at)
                VALUES ('demo_admin', ?, ?, 'admin', 1, ?);
                """,
                (hash_admin, salt_admin, now),
            )
            admin_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO user_profiles (user_id, vivedex_id, display_name, bio, external_orcid_url, created_at, updated_at)
                VALUES (?, 'VDX-DEMO-01', 'Demo Lead Curator [DEMO DATA]', 'Demonstration administrator profile for platform testing.', '', ?, ?);
                """,
                (admin_id, now, now),
            )
        else:
            admin_id = admin_row[0]

        cursor.execute("SELECT id FROM users WHERE username = 'demo_naturalist';")
        nat_row = cursor.fetchone()
        if not nat_row:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, salt, role, is_active, created_at)
                VALUES ('demo_naturalist', ?, ?, 'user', 1, ?);
                """,
                (hash_curator, salt_curator, now),
            )
            naturalist_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO user_profiles (user_id, vivedex_id, display_name, bio, external_orcid_url, created_at, updated_at)
                VALUES (?, 'VDX-DEMO-02', 'Demo Field Observer [DEMO DATA]', 'Field observer exploring regional urban biodiversity.', 'https://orcid.org/0000-0002-1825-0097', ?, ?);
                """,
                (naturalist_id, now, now),
            )
        else:
            naturalist_id = nat_row[0]

        # 2. Curated demonstration taxa
        demo_taxa = [
            (
                5231190,
                "Passer domesticus (Linnaeus, 1758)",
                "Passer domesticus",
                "House Sparrow",
                "SPECIES",
                "ACCEPTED",
                "EXACT",
                "Animalia",
                "Chordata",
                "Aves",
                "Passeriformes",
                "Passeridae",
                "Passer",
                "Passer domesticus",
            ),
            (
                1956599,
                "Erannis defoliaria (Clerck, 1759)",
                "Erannis defoliaria",
                "Mottled Umber",
                "SPECIES",
                "ACCEPTED",
                "EXACT",
                "Animalia",
                "Arthropoda",
                "Insecta",
                "Lepidoptera",
                "Geometridae",
                "Erannis",
                "Erannis defoliaria",
            ),
            (
                5133088,
                "Danaus plexippus (Linnaeus, 1758)",
                "Danaus plexippus",
                "Monarch Butterfly",
                "SPECIES",
                "ACCEPTED",
                "EXACT",
                "Animalia",
                "Arthropoda",
                "Insecta",
                "Lepidoptera",
                "Nymphalidae",
                "Danaus",
                "Danaus plexippus",
            ),
            (
                1341976,
                "Apis mellifera Linnaeus, 1758",
                "Apis mellifera",
                "Western Honey Bee",
                "SPECIES",
                "ACCEPTED",
                "EXACT",
                "Animalia",
                "Arthropoda",
                "Insecta",
                "Hymenoptera",
                "Apidae",
                "Apis",
                "Apis mellifera",
            ),
            (
                5219173,
                "Canis lupus Linnaeus, 1758",
                "Canis lupus",
                "Gray Wolf",
                "SPECIES",
                "ACCEPTED",
                "EXACT",
                "Animalia",
                "Chordata",
                "Mammalia",
                "Carnivora",
                "Canidae",
                "Canis",
                "Canis lupus",
            ),
        ]

        for (
            t_id,
            s_name,
            c_name,
            comm_name,
            rank,
            status,
            m_type,
            k,
            p,
            c,
            o,
            f,
            g,
            sp,
        ) in demo_taxa:
            cursor.execute(
                """
                INSERT INTO taxa (
                    taxon_id, scientific_name, canonical_name, common_name, rank,
                    status, match_type, kingdom, phylum, class_name, order_name,
                    family, genus, species, data_provider, licence, attribution,
                    retrieved_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'GBIF Backbone Taxonomy', 'CC BY 4.0',
                          'GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset. https://doi.org/10.15468/39omei', ?, ?)
                ON CONFLICT(taxon_id) DO UPDATE SET
                    common_name = excluded.common_name;
                """,
                (
                    t_id,
                    s_name,
                    c_name,
                    comm_name,
                    rank,
                    status,
                    m_type,
                    k,
                    p,
                    c,
                    o,
                    f,
                    g,
                    sp,
                    now,
                    now,
                ),
            )

        # 3. Create demonstration collections
        for t_id in [5231190, 1956599, 5133088, 1341976, 5219173]:
            cursor.execute(
                """
                INSERT OR IGNORE INTO collections (
                    user_id, taxon_id, first_encounter_at, last_encounter_at,
                    encounter_count, notes, created_at
                ) VALUES (?, ?, ?, ?, 1, '[DEMO DATA] Verified sample collection entry', ?);
                """,
                (naturalist_id, t_id, now, now, now),
            )

        # 4. Create demonstration observations
        demo_observations = [
            (
                "OBS-DEMO-001",
                naturalist_id,
                "Passer domesticus",
                5231190,
                "[DEMO DATA] Observed feeding on seeds on garden wall.",
                "London, UK",
                "ACCEPTED_FOR_CATALOG",
            ),
            (
                "OBS-DEMO-002",
                naturalist_id,
                "Erannis defoliaria",
                1956599,
                "[DEMO DATA] Adult moth resting on oak tree trunk in mixed woodland.",
                "Epping Forest, UK",
                "ACCEPTED_FOR_CATALOG",
            ),
            (
                "OBS-DEMO-003",
                naturalist_id,
                "Danaus plexippus",
                5133088,
                "[DEMO DATA] Perched on milkweed blossoms during afternoon migration survey.",
                "Austin, Texas, USA",
                "PENDING",
            ),
            (
                "OBS-DEMO-004",
                naturalist_id,
                "Apis mellifera",
                1341976,
                "[DEMO DATA] Foraging on lavender blooms.",
                "Cambridge, UK",
                "PENDING",
            ),
            (
                "OBS-DEMO-005",
                naturalist_id,
                "Canis lupus",
                5219173,
                "[DEMO DATA] Track identification verified by camera trap footage.",
                "Yellowstone National Park, USA",
                "NEEDS_MORE_EVIDENCE",
            ),
        ]

        dummy_model_json = json.dumps(
            {
                "model": "muse-spark-1.3 [DEMO DATA]",
                "observation_summary": "[DEMO DATA] Verified diagnostic features.",
                "candidates": [
                    {
                        "scientific_name": "Passer domesticus",
                        "common_name": "House Sparrow",
                        "visual_evidence": ["[DEMO DATA] Visual evidence marker"],
                    }
                ],
            }
        )

        dummy_gbif_json = json.dumps(
            {
                "usageKey": 5231190,
                "scientificName": "Passer domesticus (Linnaeus, 1758)",
                "matchType": "EXACT",
                "rank": "SPECIES",
            }
        )

        for obs_id, u_id, c_name, t_id, notes, loc, status in demo_observations:
            cursor.execute(
                """
                INSERT OR IGNORE INTO observations (
                    observation_id, owner_id, candidate_scientific_name, matched_taxon_id,
                    observation_timestamp, field_notes, coarse_location, model_result_json,
                    gbif_result_json, taxonomic_resolution, moderation_status, provenance,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'EXACT', ?, ?, ?);
                """,
                (
                    obs_id,
                    u_id,
                    c_name,
                    t_id,
                    now,
                    notes,
                    loc,
                    dummy_model_json,
                    dummy_gbif_json,
                    status,
                    DEMO_PROVENANCE_TAG,
                    now,
                ),
            )

    # Award eligible badges to demo user
    achievement_service.evaluate_user_achievements(naturalist_id)

    return {
        "admin_id": admin_id,
        "naturalist_id": naturalist_id,
        "demo_password": runtime_demo_secret,
        "provenance": DEMO_PROVENANCE_TAG,
    }
