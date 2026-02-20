"""Semantic graph analysis — v3 Phase 3 replacement for citation_graph.

Typed semantic relations (SUPPORTS, CONTESTS, CONTRADICTS, CITES, EXTENDS,
SUPERVISES, COAUTHORS, TRANSLATES) replace the flat citation graph. Each
relation type drives different analysis:

  - SUPPORTS → school detection (union-find)
  - CONTESTS/CONTRADICTS → fracture detection
  - CITES → authority detection (in-degree)
  - SUPERVISES/EXTENDS → influence chain detection (DFS)

No external dependencies (uses stdlib only).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from epistemix.models import Anomaly, GapType, RelationType, SemanticRelation, Severity


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ScholarNode:
    """A node in the semantic graph."""
    name: str
    in_degree: int = 0
    out_degree: int = 0
    investigated: bool = False
    languages_seen_in: set = field(default_factory=set)

    @property
    def priority(self) -> float:
        """Higher = more important to investigate."""
        if self.investigated:
            return 0.0
        return self.in_degree / (self.out_degree + 1)


@dataclass
class AcademicSchool:
    """A cluster of researchers connected by SUPPORTS relations."""
    members: list[str] = field(default_factory=list)
    size: int = 0


# ============================================================
# SEMANTIC GRAPH
# ============================================================

class SemanticGraph:
    """Typed semantic relation graph with multi-detector anomaly analysis.

    Replaces CitationGraph (v2) with typed relations. Schools are detected
    via union-find on SUPPORTS edges. Fractures via CONTESTS/CONTRADICTS.
    Authority via CITES in-degree. Influence chains via SUPERVISES/EXTENDS DFS.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, ScholarNode] = {}
        self.relations: list[SemanticRelation] = []
        self._typed_adjacency: dict[str, dict[str, list[RelationType]]] = {}

    # ----------------------------------------------------------
    # Graph population
    # ----------------------------------------------------------

    def add_relations(self, relations: list[SemanticRelation]) -> None:
        """Populate graph from a list of SemanticRelations.

        For each relation:
        - Create/update source and target nodes (case-insensitive keys)
        - Update in/out degree
        - Track languages seen
        - Store in typed adjacency map
        """
        for rel in relations:
            self.relations.append(rel)

            src_key = rel.source.lower().strip()
            tgt_key = rel.target.lower().strip()

            # Create or update source node
            if src_key not in self.nodes:
                self.nodes[src_key] = ScholarNode(
                    name=rel.source,
                    languages_seen_in={rel.language},
                )
            else:
                self.nodes[src_key].languages_seen_in.add(rel.language)
            self.nodes[src_key].out_degree += 1

            # Create or update target node
            if tgt_key not in self.nodes:
                self.nodes[tgt_key] = ScholarNode(
                    name=rel.target,
                    languages_seen_in={rel.language},
                )
            else:
                self.nodes[tgt_key].languages_seen_in.add(rel.language)
            self.nodes[tgt_key].in_degree += 1

            # Update typed adjacency
            if src_key not in self._typed_adjacency:
                self._typed_adjacency[src_key] = {}
            if tgt_key not in self._typed_adjacency[src_key]:
                self._typed_adjacency[src_key][tgt_key] = []
            self._typed_adjacency[src_key][tgt_key].append(rel.relation)

    # ----------------------------------------------------------
    # School detection (union-find on SUPPORTS)
    # ----------------------------------------------------------

    def detect_schools(self) -> list[AcademicSchool]:
        """Detect academic schools using union-find on SUPPORTS relations.

        Any SUPPORTS edge (A supports B) unions the two nodes. Connected
        components of size >= 2 are schools. Sorted by size descending.
        """
        parent: dict[str, str] = {}

        def find(x: str) -> str:
            if x not in parent:
                parent[x] = x
            while parent[x] != x:
                parent[x] = parent[parent[x]]  # path compression
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        # Initialize all nodes
        for name in self.nodes:
            parent[name] = name

        # Union pairs connected by SUPPORTS
        for rel in self.relations:
            if rel.relation == RelationType.SUPPORTS:
                src_key = rel.source.lower().strip()
                tgt_key = rel.target.lower().strip()
                union(src_key, tgt_key)

        # Group by root
        groups: dict[str, list[str]] = {}
        for name in self.nodes:
            root = find(name)
            groups.setdefault(root, []).append(name)

        schools = []
        for members in groups.values():
            if len(members) >= 2:
                schools.append(AcademicSchool(
                    members=sorted(members),
                    size=len(members),
                ))

        return sorted(schools, key=lambda s: -s.size)

    # ----------------------------------------------------------
    # Fracture detection (CONTESTS/CONTRADICTS)
    # ----------------------------------------------------------

    def detect_fractures(self) -> list[tuple[str, str]]:
        """Find all CONTESTS or CONTRADICTS pairs.

        Deduplicates (A,B) and (B,A) — returns canonical sorted tuples.
        """
        seen: set[tuple[str, str]] = set()
        fractures: list[tuple[str, str]] = []

        for rel in self.relations:
            if rel.relation in (RelationType.CONTESTS, RelationType.CONTRADICTS):
                src_key = rel.source.lower().strip()
                tgt_key = rel.target.lower().strip()
                pair = tuple(sorted((src_key, tgt_key)))
                if pair not in seen:
                    seen.add(pair)
                    fractures.append(pair)

        return fractures

    # ----------------------------------------------------------
    # Authority detection (high CITES in-degree)
    # ----------------------------------------------------------

    def detect_authority(self, min_cites: int = 3) -> list[ScholarNode]:
        """Find nodes with high CITES-specific in-degree.

        Only counts CITES relations (not SUPPORTS, EXTENDS, etc.).
        Sorted by CITES in-degree descending.
        """
        cites_in: dict[str, int] = {}

        for rel in self.relations:
            if rel.relation == RelationType.CITES:
                tgt_key = rel.target.lower().strip()
                cites_in[tgt_key] = cites_in.get(tgt_key, 0) + 1

        authorities = []
        for key, count in cites_in.items():
            if count >= min_cites and key in self.nodes:
                authorities.append(self.nodes[key])

        return sorted(authorities, key=lambda n: -cites_in.get(n.name.lower().strip(), 0))

    # ----------------------------------------------------------
    # Isolated node detection
    # ----------------------------------------------------------

    def detect_isolated(self) -> list[ScholarNode]:
        """Find nodes that are neither source nor target of any relation."""
        connected: set[str] = set()
        for rel in self.relations:
            connected.add(rel.source.lower().strip())
            connected.add(rel.target.lower().strip())

        return [
            node for key, node in self.nodes.items()
            if key not in connected
        ]

    # ----------------------------------------------------------
    # Influence chain detection (SUPERVISES/EXTENDS DFS)
    # ----------------------------------------------------------

    def detect_influence_chains(self, min_length: int = 2) -> list[list[str]]:
        """Find paths in the SUPERVISES/EXTENDS subgraph.

        Uses DFS to find all maximal paths of length >= min_length (edges).
        Deduplicates by removing subpaths that are contained in longer chains.
        """
        # Build directed adjacency for SUPERVISES/EXTENDS only
        influence_adj: dict[str, list[str]] = {}
        for rel in self.relations:
            if rel.relation in (RelationType.SUPERVISES, RelationType.EXTENDS):
                src_key = rel.source.lower().strip()
                tgt_key = rel.target.lower().strip()
                influence_adj.setdefault(src_key, []).append(tgt_key)

        if not influence_adj:
            return []

        # Find all maximal paths via DFS
        all_paths: list[list[str]] = []

        # Identify start nodes (have outgoing edges in influence subgraph)
        # Start from nodes that have no incoming influence edges
        has_incoming: set[str] = set()
        for targets in influence_adj.values():
            for t in targets:
                has_incoming.add(t)

        start_nodes = [n for n in influence_adj if n not in has_incoming]
        # Also try all nodes with outgoing edges as starts (for cycles)
        if not start_nodes:
            start_nodes = list(influence_adj.keys())

        for start in start_nodes:
            self._dfs_paths(start, influence_adj, [start], all_paths)

        # Filter by min_length (number of edges = len(path) - 1)
        valid = [p for p in all_paths if len(p) - 1 >= min_length]

        # Deduplicate: remove subpaths of longer chains
        if not valid:
            return []

        # Sort longest first for dedup
        valid.sort(key=len, reverse=True)
        maximal: list[list[str]] = []
        for path in valid:
            is_subpath = False
            path_tuple = tuple(path)
            for longer in maximal:
                longer_str = ",".join(longer)
                path_str = ",".join(path)
                if path_str in longer_str:
                    is_subpath = True
                    break
            if not is_subpath:
                maximal.append(path)

        return maximal

    def _dfs_paths(
        self,
        current: str,
        adj: dict[str, list[str]],
        path: list[str],
        results: list[list[str]],
    ) -> None:
        """DFS helper: collect all maximal paths from current node."""
        extended = False
        if current in adj:
            for neighbor in adj[current]:
                if neighbor not in path:  # avoid cycles
                    path.append(neighbor)
                    self._dfs_paths(neighbor, adj, path, results)
                    path.pop()
                    extended = True

        if not extended and len(path) >= 2:
            results.append(list(path))

    # ----------------------------------------------------------
    # Unmapped pair detection
    # ----------------------------------------------------------

    def detect_unmapped_pairs(self, min_mentions: int = 2) -> list[tuple[str, str]]:
        """Find pairs of entities with sufficient mentions but no direct relation.

        An entity's "mentions" = in_degree + out_degree. Pairs where both
        entities have >= min_mentions but no relation between them are unmapped.
        """
        # Find qualifying entities
        qualifying = [
            key for key, node in self.nodes.items()
            if (node.in_degree + node.out_degree) >= min_mentions
        ]

        # Build set of related pairs (bidirectional check)
        related: set[tuple[str, str]] = set()
        for rel in self.relations:
            src_key = rel.source.lower().strip()
            tgt_key = rel.target.lower().strip()
            related.add((src_key, tgt_key))
            related.add((tgt_key, src_key))

        # Find unmapped pairs
        unmapped: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for i, a in enumerate(qualifying):
            for b in qualifying[i + 1:]:
                if (a, b) not in related and (b, a) not in related:
                    pair = tuple(sorted((a, b)))
                    if pair not in seen:
                        seen.add(pair)
                        unmapped.append(pair)

        return unmapped

    # ----------------------------------------------------------
    # Anomaly generation
    # ----------------------------------------------------------

    def generate_anomalies(self) -> list[Anomaly]:
        """Combine all detectors into a list of Anomaly objects.

        - Fractures -> FRACTURE_LINE, Severity.MEDIUM
        - High-citation uninvestigated scholars -> CITATION_ISLAND, Severity.HIGH
        - Single school with size >= 3 -> SCHOOL_GAP, Severity.CRITICAL
        """
        anomalies: list[Anomaly] = []

        # Fractures
        fractures = self.detect_fractures()
        for src, tgt in fractures:
            src_name = self.nodes[src].name if src in self.nodes else src
            tgt_name = self.nodes[tgt].name if tgt in self.nodes else tgt
            anomalies.append(Anomaly(
                description=(
                    f"Fracture between '{src_name}' and '{tgt_name}': "
                    f"contested or contradicted claims"
                ),
                gap_type=GapType.FRACTURE_LINE,
                severity=Severity.MEDIUM,
                recommendation=(
                    f"Investigate the disagreement between "
                    f"{src_name} and {tgt_name}"
                ),
            ))

        # High-citation uninvestigated (authority detection)
        authorities = self.detect_authority(min_cites=3)
        for node in authorities:
            if not node.investigated:
                anomalies.append(Anomaly(
                    description=(
                        f"Scholar '{node.name}' cited "
                        f"{self._cites_in_degree(node.name)}x "
                        f"but never investigated"
                    ),
                    gap_type=GapType.CITATION_ISLAND,
                    severity=Severity.HIGH,
                    recommendation=f"Search for publications by {node.name}",
                    suggested_queries=[
                        f"{node.name} publications research",
                        f"{node.name} academic paper",
                    ],
                ))

        # School imbalance (echo chamber)
        schools = self.detect_schools()
        if len(schools) == 1 and schools[0].size >= 3:
            anomalies.append(Anomaly(
                description=(
                    f"Only one citation school detected "
                    f"({schools[0].size} members). "
                    "Possible echo chamber."
                ),
                gap_type=GapType.SCHOOL_GAP,
                severity=Severity.CRITICAL,
                recommendation="Search for alternative research groups",
            ))

        return anomalies

    def _cites_in_degree(self, name: str) -> int:
        """Count CITES-specific in-degree for a given node."""
        key = name.lower().strip()
        count = 0
        for rel in self.relations:
            if rel.relation == RelationType.CITES and rel.target.lower().strip() == key:
                count += 1
        return count

    # ----------------------------------------------------------
    # Summary
    # ----------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        """Summary statistics for the semantic graph."""
        schools = self.detect_schools()
        fractures = self.detect_fractures()
        isolated = self.detect_isolated()

        # Count relation types
        type_counts: dict[str, int] = {}
        for rel in self.relations:
            rt = rel.relation.value
            type_counts[rt] = type_counts.get(rt, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_relations": len(self.relations),
            "schools": len(schools),
            "school_sizes": [s.size for s in schools],
            "fractures": len(fractures),
            "isolated_scholars": len(isolated),
            "relation_types": type_counts,
        }
