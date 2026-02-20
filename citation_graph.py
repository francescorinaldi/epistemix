"""
EPISTEMIX v2 — Citation Graph Module

Builds a directed graph of citations between scholars.
Derives:
  - Citation weight: scholars cited by many independent
    sources should be investigated with higher priority
  - School detection: clusters of mutual citation suggest
    academic "schools" — if you find one school, expect
    at least one opposing school
  - Isolation detection: a scholar cited by no one (or
    citing no one found) may be peripheral or may indicate
    a missing connection
"""

from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from core import Finding, Entity, EntityType, Severity, Anomaly, GapType


@dataclass
class CitationEdge:
    """A directed citation: source_author cites target."""
    source_author: str
    target: str
    source_document: str
    weight: float = 1.0


@dataclass
class ScholarNode:
    """A node in the citation graph."""
    name: str
    cited_by: set = field(default_factory=set)    # who cites this scholar
    cites: set = field(default_factory=set)        # who this scholar cites
    in_degree: int = 0     # times cited by others
    out_degree: int = 0    # times cites others
    investigated: bool = False

    @property
    def total_degree(self) -> int:
        return self.in_degree + self.out_degree

    @property
    def citation_priority(self) -> float:
        """
        Higher = more urgent to investigate.
        Cited by many but not investigated = high priority.
        """
        if self.investigated:
            return 0.0
        return self.in_degree * 2.0 + self.out_degree * 0.5


@dataclass
class AcademicSchool:
    """A cluster of mutually-citing scholars."""
    members: set = field(default_factory=set)
    internal_edges: int = 0
    label: str = ""

    @property
    def size(self) -> int:
        return len(self.members)


class CitationGraph:
    """
    Builds and analyzes a citation graph from findings.
    """

    def __init__(self):
        self.nodes: dict[str, ScholarNode] = {}
        self.edges: list[CitationEdge] = []
        self._known_non_scholars: set = set()

    def register_non_scholars(self, names: set[str]):
        """Register names that should not be treated as scholars."""
        self._known_non_scholars = {n.lower() for n in names}

    def build_from_findings(
        self, findings: list[Finding], entities: dict[str, Entity]
    ):
        """
        Build the citation graph from findings.
        Logic: if finding has author A and mentions entity B
        (where B is a scholar), then A → B is a citation edge.
        """
        # Identify which entities are scholars
        scholar_names = set()
        for key, entity in entities.items():
            if entity.entity_type == EntityType.SCHOLAR:
                scholar_names.add(key)

        for finding in findings:
            if not finding.author:
                continue

            author_key = finding.author.lower()

            # Ensure author node exists
            if author_key not in self.nodes:
                self.nodes[author_key] = ScholarNode(
                    name=finding.author
                )

            # Mark as investigated (they have a publication)
            self.nodes[author_key].investigated = True

            # Each mentioned scholar is a citation
            for mentioned in finding.entities_mentioned:
                m_key = mentioned.lower()

                # Skip self-citation and non-scholars
                if m_key == author_key:
                    continue
                if m_key in self._known_non_scholars:
                    continue
                if m_key not in scholar_names:
                    continue

                # Ensure target node exists
                if m_key not in self.nodes:
                    self.nodes[m_key] = ScholarNode(
                        name=mentioned
                    )
                    # Check investigation status
                    if m_key in entities:
                        self.nodes[m_key].investigated = (
                            entities[m_key].investigated
                        )

                # Add edge
                edge = CitationEdge(
                    source_author=finding.author,
                    target=mentioned,
                    source_document=finding.source,
                )
                self.edges.append(edge)

                # Update degrees
                self.nodes[author_key].cites.add(m_key)
                self.nodes[author_key].out_degree += 1
                self.nodes[m_key].cited_by.add(author_key)
                self.nodes[m_key].in_degree += 1

    def get_priority_uninvestigated(
        self, top_n: int = 5
    ) -> list[ScholarNode]:
        """
        Scholars not yet investigated, ranked by citation
        priority (cited by many = investigate first).
        """
        uninvestigated = [
            n for n in self.nodes.values()
            if not n.investigated and n.citation_priority > 0
        ]
        uninvestigated.sort(
            key=lambda n: n.citation_priority, reverse=True
        )
        return uninvestigated[:top_n]

    def detect_schools(self) -> list[AcademicSchool]:
        """
        Simple school detection via mutual citation.
        If A cites B and B cites A, they are in the same school.
        Transitive: if A↔B and B↔C, then {A,B,C} is a school.
        """
        # Find mutual citation pairs
        mutual_pairs = []
        for node_key, node in self.nodes.items():
            for cited_key in node.cites:
                if cited_key in self.nodes:
                    cited_node = self.nodes[cited_key]
                    if node_key in cited_node.cites:
                        mutual_pairs.append(
                            (node_key, cited_key)
                        )

        if not mutual_pairs:
            return []

        # Union-Find to group into schools
        parent = {}

        def find(x):
            if x not in parent:
                parent[x] = x
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        for a, b in mutual_pairs:
            union(a, b)

        # Group by root
        groups = defaultdict(set)
        for key in parent:
            groups[find(key)].add(key)

        schools = []
        for members in groups.values():
            if len(members) >= 2:
                # Count internal edges
                internal = sum(
                    1 for a, b in mutual_pairs
                    if a in members and b in members
                )
                school = AcademicSchool(
                    members={
                        self.nodes[m].name for m in members
                    },
                    internal_edges=internal,
                )
                schools.append(school)

        return schools

    def detect_isolated_scholars(self) -> list[ScholarNode]:
        """
        Scholars who are investigated (have publications)
        but are neither cited by nor cite anyone else found.
        This may indicate a missing connection or a truly
        independent voice.
        """
        return [
            n for n in self.nodes.values()
            if n.investigated and n.total_degree == 0
        ]

    def generate_anomalies(self) -> list[Anomaly]:
        """Generate anomalies from graph analysis."""
        anomalies = []

        # 1. High-priority uninvestigated scholars
        priority = self.get_priority_uninvestigated(5)
        for scholar in priority:
            if scholar.in_degree >= 2:
                anomalies.append(Anomaly(
                    description=(
                        f"Scholar '{scholar.name}' cited by "
                        f"{scholar.in_degree} sources but not "
                        f"investigated (cited by: "
                        f"{', '.join(sorted(scholar.cited_by))})"
                    ),
                    gap_type=GapType.ENTITY_UNRESEARCHED,
                    severity=Severity.HIGH,
                    recommendation=(
                        f"Search for publications by "
                        f"{scholar.name}"
                    ),
                ))

        # 2. School imbalance
        schools = self.detect_schools()
        if len(schools) == 1:
            anomalies.append(Anomaly(
                description=(
                    f"Only one academic school detected: "
                    f"{', '.join(sorted(schools[0].members))}. "
                    f"Expect at least one opposing school."
                ),
                gap_type=GapType.VOICE,
                severity=Severity.MEDIUM,
                recommendation=(
                    "Search for scholars who disagree with "
                    "this group's conclusions"
                ),
            ))

        # 3. Very high in-degree without investigation
        for node in self.nodes.values():
            if node.in_degree >= 3 and not node.investigated:
                anomalies.append(Anomaly(
                    description=(
                        f"Scholar '{node.name}' has high "
                        f"citation count ({node.in_degree}) "
                        f"but zero publications found — "
                        f"critical gap"
                    ),
                    gap_type=GapType.ENTITY_UNRESEARCHED,
                    severity=Severity.CRITICAL,
                    recommendation=(
                        f"Urgently search for {node.name}'s "
                        f"publications"
                    ),
                ))

        return anomalies

    def summary(self) -> str:
        """Human-readable summary of the graph."""
        lines = []
        lines.append(
            f"Scholars in graph: {len(self.nodes)}"
        )
        lines.append(f"Citation edges: {len(self.edges)}")

        investigated = sum(
            1 for n in self.nodes.values() if n.investigated
        )
        lines.append(
            f"Investigated: {investigated}/{len(self.nodes)}"
        )

        # Top cited
        by_in = sorted(
            self.nodes.values(),
            key=lambda n: n.in_degree, reverse=True
        )
        if by_in:
            lines.append("Top cited scholars:")
            for n in by_in[:5]:
                status = "✓" if n.investigated else "✗"
                lines.append(
                    f"  [{status}] {n.name}: cited by "
                    f"{n.in_degree}, cites {n.out_degree}"
                )

        # Schools
        schools = self.detect_schools()
        if schools:
            lines.append(f"Academic schools detected: {len(schools)}")
            for i, s in enumerate(schools):
                lines.append(
                    f"  School {i+1}: "
                    f"{', '.join(sorted(s.members))}"
                )
        else:
            lines.append(
                "No mutual citation clusters detected"
            )

        return "\n".join(lines)
