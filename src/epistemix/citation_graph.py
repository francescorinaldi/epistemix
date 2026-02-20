"""Citation graph analysis — detect schools, islands, and priority rankings.

Based on the founder's v2 design with:
  - ScholarNode with investigation status and priority scoring
  - Union-find school detection (mutual citation = same school)
  - Non-scholar entity filtering
  - Priority-ranked uninvestigated entities

No external dependencies (uses stdlib only).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from epistemix.models import Anomaly, Finding, GapType, Severity


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class CitationEdge:
    """A citation link: source cites target."""
    source: str
    target: str
    source_language: str = ""


@dataclass
class ScholarNode:
    """A node in the citation graph."""
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
    """A cluster of mutually-citing researchers."""
    members: list[str] = field(default_factory=list)
    size: int = 0


# ============================================================
# CITATION GRAPH
# ============================================================

class CitationGraph:
    """Directed citation graph with school detection and priority ranking.

    Schools are detected via mutual citation (A cites B AND B cites A)
    using a union-find algorithm — more accurate than simple connected
    components.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, ScholarNode] = {}
        self.edges: list[CitationEdge] = []
        self._adjacency: dict[str, set[str]] = {}
        self._reverse: dict[str, set[str]] = {}
        self._non_scholars: set[str] = set()

    def register_non_scholars(self, names: set[str]) -> None:
        """Register names that should not be treated as scholars."""
        self._non_scholars = {n.lower() for n in names}

    def build_from_findings(self, findings: list[Finding]) -> None:
        """Build graph from a list of findings."""
        for finding in findings:
            author = finding.author.lower().strip() if finding.author else ""
            if not author or author in self._non_scholars:
                continue

            # Ensure author node exists
            if author not in self.nodes:
                self.nodes[author] = ScholarNode(
                    name=finding.author,
                    investigated=True,  # We have their publication
                    languages_seen_in={finding.language},
                )
            else:
                self.nodes[author].investigated = True
                self.nodes[author].languages_seen_in.add(finding.language)

            # Process mentioned entities as citation targets
            for mentioned in finding.entities_mentioned:
                target = mentioned.lower().strip()
                if target in self._non_scholars or target == author:
                    continue

                # Ensure target node exists
                if target not in self.nodes:
                    self.nodes[target] = ScholarNode(
                        name=mentioned,
                        languages_seen_in={finding.language},
                    )
                else:
                    self.nodes[target].languages_seen_in.add(finding.language)

                # Add edge
                self.edges.append(CitationEdge(
                    source=author, target=target,
                    source_language=finding.language,
                ))

                # Update degrees
                self.nodes[author].out_degree += 1
                self.nodes[target].in_degree += 1

                # Update adjacency
                self._adjacency.setdefault(author, set()).add(target)
                self._reverse.setdefault(target, set()).add(author)

    def detect_schools(self) -> list[AcademicSchool]:
        """Detect academic schools using union-find on mutual citations.

        A mutual citation means A cites B AND B cites A.
        """
        # Union-find
        parent: dict[str, str] = {}

        def find(x: str) -> str:
            if x not in parent:
                parent[x] = x
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        # Initialize all nodes
        for name in self.nodes:
            parent[name] = name

        # Union mutually-citing pairs
        for source, targets in self._adjacency.items():
            for target in targets:
                if target in self._adjacency and source in self._adjacency[target]:
                    union(source, target)

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

    def detect_isolated_scholars(self) -> list[ScholarNode]:
        """Find scholars with high in-degree but not investigated."""
        return [
            node for node in self.nodes.values()
            if not node.investigated and node.in_degree >= 2
        ]

    def get_priority_uninvestigated(self, limit: int = 10) -> list[ScholarNode]:
        """Top uninvestigated scholars ranked by priority."""
        uninvestigated = [
            n for n in self.nodes.values() if not n.investigated
        ]
        return sorted(
            uninvestigated, key=lambda n: -n.priority
        )[:limit]

    def generate_anomalies(self) -> list[Anomaly]:
        """Generate anomalies from the citation graph."""
        anomalies: list[Anomaly] = []

        # High-priority uninvestigated scholars
        priority = self.get_priority_uninvestigated(5)
        for node in priority:
            if node.in_degree >= 3:
                anomalies.append(Anomaly(
                    description=(
                        f"Scholar '{node.name}' cited {node.in_degree}x "
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

        # School imbalance
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

    def summary(self) -> dict[str, Any]:
        """Summary statistics."""
        schools = self.detect_schools()
        isolated = self.detect_isolated_scholars()
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "schools": len(schools),
            "school_sizes": [s.size for s in schools],
            "isolated_scholars": len(isolated),
            "uninvestigated": len([
                n for n in self.nodes.values() if not n.investigated
            ]),
        }
