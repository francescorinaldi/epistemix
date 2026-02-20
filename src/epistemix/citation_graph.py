"""Citation graph analysis — detect schools, islands, and priority rankings.

Uses a directed adjacency list (no external dependencies).
A "school" is a cluster of mutually citing researchers.
A "citation island" is a scholar frequently cited but never directly searched.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from epistemix.models import (
    Anomaly,
    AnomalyType,
    Finding,
    FindingType,
    Severity,
)


@dataclass
class CitationGraph:
    """Directed citation graph built from findings."""

    # node → set of nodes it cites
    _adjacency: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    # node → set of nodes that cite it
    _reverse: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    # names of scholars discovered via direct search queries
    _searched: set[str] = field(default_factory=set)

    def add_finding(self, finding: Finding) -> None:
        """Register a finding and its citations in the graph."""
        name = finding.name.lower().strip()
        # Ensure node exists even without edges
        if name not in self._adjacency:
            self._adjacency[name] = set()

        if finding.source_query:
            self._searched.add(name)

        for cited in finding.citations:
            cited_norm = cited.lower().strip()
            self._adjacency[name].add(cited_norm)
            self._reverse[cited_norm].add(name)
            # Ensure cited node exists
            if cited_norm not in self._adjacency:
                self._adjacency[cited_norm] = set()

    @property
    def nodes(self) -> set[str]:
        return set(self._adjacency.keys())

    @property
    def node_count(self) -> int:
        return len(self._adjacency)

    def in_degree(self, node: str) -> int:
        return len(self._reverse.get(node.lower().strip(), set()))

    def out_degree(self, node: str) -> int:
        return len(self._adjacency.get(node.lower().strip(), set()))

    def detect_schools(self) -> list[set[str]]:
        """Find citation clusters via connected components on the undirected projection.

        A school is a group of scholars who cite each other. We build an
        undirected graph (A↔B if A cites B or B cites A) and find connected
        components using BFS.
        """
        # Build undirected adjacency
        undirected: dict[str, set[str]] = defaultdict(set)
        for node, cited_set in self._adjacency.items():
            for cited in cited_set:
                undirected[node].add(cited)
                undirected[cited].add(node)

        visited: set[str] = set()
        schools: list[set[str]] = []

        for node in undirected:
            if node in visited:
                continue
            # BFS
            component: set[str] = set()
            queue = deque([node])
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)
                for neighbor in undirected[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            if len(component) >= 2:
                schools.append(component)

        return schools

    def check_single_school(self) -> Anomaly | None:
        """Return a CRITICAL anomaly if only one citation school exists."""
        schools = self.detect_schools()
        if len(schools) == 1:
            return Anomaly(
                id="A-CG-single-school",
                anomaly_type=AnomalyType.SCHOOL_GAP,
                severity=Severity.CRITICAL,
                description=(
                    f"Only one citation school detected ({len(schools[0])} scholars). "
                    "This suggests the search has not yet reached beyond a single "
                    "research community."
                ),
                suggested_queries=[
                    "alternative research groups",
                    "competing interpretations",
                ],
            )
        return None

    def find_citation_islands(self, min_citations: int = 2) -> list[dict[str, int | str]]:
        """Find scholars cited by others but never directly searched.

        A citation island is someone who appears in citations but was not
        found via any direct search query — a potential blind spot.
        """
        islands = []
        for node in self.nodes:
            in_deg = self.in_degree(node)
            if in_deg >= min_citations and node not in self._searched:
                islands.append({
                    "name": node,
                    "in_citations": in_deg,
                    "direct_searches": 0,
                })
        return sorted(islands, key=lambda x: x["in_citations"], reverse=True)

    def investigation_priority_ranking(self) -> list[dict[str, float | str]]:
        """Rank all nodes by investigation priority.

        Priority = in_citations / (direct_searches + 1)
        High priority = cited often but rarely searched directly.
        """
        rankings = []
        for node in self.nodes:
            in_deg = self.in_degree(node)
            direct = 1 if node in self._searched else 0
            priority = in_deg / (direct + 1)
            rankings.append({
                "name": node,
                "in_citations": in_deg,
                "direct_searches": direct,
                "priority": round(priority, 2),
            })
        return sorted(rankings, key=lambda x: x["priority"], reverse=True)

    def generate_anomalies(self) -> list[Anomaly]:
        """Generate all citation-graph-based anomalies."""
        anomalies = []

        # Check single school
        single_school = self.check_single_school()
        if single_school:
            anomalies.append(single_school)

        # Check citation islands
        islands = self.find_citation_islands()
        for island in islands:
            anomalies.append(Anomaly(
                id=f"A-CG-island-{island['name'][:20]}",
                anomaly_type=AnomalyType.CITATION_ISLAND,
                severity=Severity.HIGH,
                description=(
                    f"Scholar '{island['name']}' is cited {island['in_citations']} times "
                    "but was never directly searched — potential blind spot."
                ),
                suggested_queries=[
                    f"{island['name']} publications",
                    f"{island['name']} research contributions",
                ],
            ))

        return anomalies
