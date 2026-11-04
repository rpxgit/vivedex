"""Lightweight SQLite-backed taxonomic and platform knowledge graph for Vivédex.

Represents entities as typed nodes and explicit relationships.
Generates genuine taxonomic edges without external graph databases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.database import Database
from src.models import TaxonRecord


@dataclass(frozen=True)
class GraphNode:
    """Represents a node in the Vivédex knowledge graph."""

    id: str
    node_type: str  # 'Taxon', 'Observation', 'User', 'Source', 'Badge'
    label: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    """Represents a directed relationship edge between two nodes."""

    source_id: str
    target_id: str
    relationship_type: str  # 'PARENT_OF', 'SYNONYM_OF', 'OBSERVED_IN', 'RECORDED_BY', 'COLLECTED_BY', 'DERIVED_FROM', 'AWARDED_TO'
    properties: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraphService:
    """Queries and traverses nodes and relationship edges stored in SQLite."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def get_taxon_by_id(self, taxon_id: int) -> TaxonRecord | None:
        """Fetch a taxon record by its integer taxon ID."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, taxon_id, scientific_name, canonical_name, common_name, rank,
                       status, match_type, kingdom, phylum, class_name, order_name,
                       family, genus, species, authorship, source_id, data_provider,
                       licence, attribution, retrieved_at, created_at
                FROM taxa
                WHERE taxon_id = ?;
                """,
                (taxon_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return TaxonRecord(
                id=row["id"],
                taxon_id=row["taxon_id"],
                scientific_name=row["scientific_name"],
                canonical_name=row["canonical_name"],
                common_name=row["common_name"],
                rank=row["rank"],
                status=row["status"],
                match_type=row["match_type"],
                kingdom=row["kingdom"],
                phylum=row["phylum"],
                class_name=row["class_name"],
                order_name=row["order_name"],
                family=row["family"],
                genus=row["genus"],
                species=row["species"],
                authorship=row["authorship"],
                source_id=row["source_id"],
                data_provider=row["data_provider"],
                licence=row["licence"],
                attribution=row["attribution"],
                retrieved_at=row["retrieved_at"],
                created_at=row["created_at"],
            )

    def get_taxon_lineage(self, taxon_id: int) -> list[TaxonRecord]:
        """Traverse upwards to retrieve the taxonomic lineage for a given taxon."""
        lineage: list[TaxonRecord] = []
        visited = set()
        current_id: int | None = taxon_id

        while current_id is not None and current_id not in visited:
            visited.add(current_id)
            taxon = self.get_taxon_by_id(current_id)
            if not taxon:
                break
            lineage.insert(0, taxon)

            # Query parent via taxon_relationships
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT parent_taxon_id
                    FROM taxon_relationships
                    WHERE child_taxon_id = ? AND relationship_type = 'PARENT_OF';
                    """,
                    (current_id,),
                )
                row = cursor.fetchone()
                current_id = row[0] if row else None

        return lineage

    def get_parent_taxon(self, child_taxon_id: int) -> TaxonRecord | None:
        """Fetch direct parent taxon."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT parent_taxon_id
                FROM taxon_relationships
                WHERE child_taxon_id = ? AND relationship_type = 'PARENT_OF';
                """,
                (child_taxon_id,),
            )
            row = cursor.fetchone()
            if row:
                return self.get_taxon_by_id(row[0])
            return None

    def get_child_taxa(self, parent_taxon_id: int) -> list[TaxonRecord]:
        """Fetch all direct child taxa."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT child_taxon_id
                FROM taxon_relationships
                WHERE parent_taxon_id = ? AND relationship_type = 'PARENT_OF';
                """,
                (parent_taxon_id,),
            )
            child_ids = [row[0] for row in cursor.fetchall()]

        children: list[TaxonRecord] = []
        for cid in child_ids:
            t = self.get_taxon_by_id(cid)
            if t:
                children.append(t)
        return children

    def get_taxon_neighborhood(self, taxon_id: int) -> dict[str, Any]:
        """Retrieve complete graph neighborhood around a taxon."""
        target_taxon = self.get_taxon_by_id(taxon_id)
        if not target_taxon:
            return {"nodes": [], "edges": []}

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        # 1. Target Taxon Node
        taxon_node_id = f"Taxon:{taxon_id}"
        nodes.append(
            GraphNode(
                id=taxon_node_id,
                node_type="Taxon",
                label=target_taxon.scientific_name,
                properties={
                    "rank": target_taxon.rank,
                    "family": target_taxon.family,
                    "canonical_name": target_taxon.canonical_name,
                },
            )
        )

        # 2. Source Node & DERIVED_FROM
        source_node_id = "Source:GBIF"
        nodes.append(
            GraphNode(
                id=source_node_id,
                node_type="Source",
                label=target_taxon.data_provider,
                properties={
                    "licence": target_taxon.licence,
                    "attribution": target_taxon.attribution,
                },
            )
        )
        edges.append(
            GraphEdge(
                source_id=taxon_node_id,
                target_id=source_node_id,
                relationship_type="DERIVED_FROM",
            )
        )

        # 3. Parent Taxon Node & PARENT_OF
        parent = self.get_parent_taxon(taxon_id)
        if parent and parent.taxon_id:
            parent_node_id = f"Taxon:{parent.taxon_id}"
            nodes.append(
                GraphNode(
                    id=parent_node_id,
                    node_type="Taxon",
                    label=parent.scientific_name,
                    properties={"rank": parent.rank},
                )
            )
            edges.append(
                GraphEdge(
                    source_id=parent_node_id,
                    target_id=taxon_node_id,
                    relationship_type="PARENT_OF",
                )
            )

        # 4. Child Taxa Nodes & PARENT_OF
        for child in self.get_child_taxa(taxon_id):
            if child.taxon_id:
                c_node_id = f"Taxon:{child.taxon_id}"
                nodes.append(
                    GraphNode(
                        id=c_node_id,
                        node_type="Taxon",
                        label=child.scientific_name,
                        properties={"rank": child.rank},
                    )
                )
                edges.append(
                    GraphEdge(
                        source_id=taxon_node_id,
                        target_id=c_node_id,
                        relationship_type="PARENT_OF",
                    )
                )

        # 5. Connected Observations & OBSERVED_IN / RECORDED_BY
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT o.observation_id, o.owner_id, u.username, o.observation_timestamp, o.moderation_status
                FROM observations o
                JOIN users u ON o.owner_id = u.id
                WHERE o.matched_taxon_id = ?
                LIMIT 10;
                """,
                (taxon_id,),
            )
            for row in cursor.fetchall():
                obs_id = row["observation_id"]
                user_id = row["owner_id"]
                username = row["username"]

                obs_node_id = f"Observation:{obs_id}"
                nodes.append(
                    GraphNode(
                        id=obs_node_id,
                        node_type="Observation",
                        label=obs_id,
                        properties={
                            "timestamp": row["observation_timestamp"],
                            "status": row["moderation_status"],
                        },
                    )
                )
                edges.append(
                    GraphEdge(
                        source_id=obs_node_id,
                        target_id=taxon_node_id,
                        relationship_type="OBSERVED_IN",
                    )
                )

                user_node_id = f"User:{user_id}"
                if not any(n.id == user_node_id for n in nodes):
                    nodes.append(
                        GraphNode(
                            id=user_node_id,
                            node_type="User",
                            label=username,
                        )
                    )
                edges.append(
                    GraphEdge(
                        source_id=obs_node_id,
                        target_id=user_node_id,
                        relationship_type="RECORDED_BY",
                    )
                )

            # 6. Connected Collectors & COLLECTED_BY
            cursor.execute(
                """
                SELECT c.user_id, u.username, c.encounter_count
                FROM collections c
                JOIN users u ON c.user_id = u.id
                WHERE c.taxon_id = ?
                LIMIT 10;
                """,
                (taxon_id,),
            )
            for row in cursor.fetchall():
                u_id = row["user_id"]
                u_name = row["username"]
                enc_count = row["encounter_count"]

                user_node_id = f"User:{u_id}"
                if not any(n.id == user_node_id for n in nodes):
                    nodes.append(
                        GraphNode(
                            id=user_node_id,
                            node_type="User",
                            label=u_name,
                        )
                    )
                edges.append(
                    GraphEdge(
                        source_id=user_node_id,
                        target_id=taxon_node_id,
                        relationship_type="COLLECTED_BY",
                        properties={"encounters": enc_count},
                    )
                )

        return {"nodes": nodes, "edges": edges}
