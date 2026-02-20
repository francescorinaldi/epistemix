"""Tests for citation graph analysis."""

from epistemix.citation_graph import CitationGraph
from epistemix.models import (
    AnomalyType,
    Finding,
    FindingType,
    QueryLanguage,
    Severity,
)


def _scholar(name: str, citations: list[str] | None = None, query: str = "test") -> Finding:
    return Finding(
        name=name,
        finding_type=FindingType.SCHOLAR,
        source_query=query,
        citations=citations or [],
    )


class TestCitationGraph:
    def test_add_finding(self):
        g = CitationGraph()
        g.add_finding(_scholar("Alice", ["Bob", "Carol"]))
        assert g.node_count == 3
        assert g.in_degree("Bob") == 1
        assert g.in_degree("Carol") == 1
        assert g.out_degree("Alice") == 2

    def test_detect_schools_two_components(self):
        g = CitationGraph()
        # School 1: Alice ↔ Bob
        g.add_finding(_scholar("Alice", ["Bob"]))
        g.add_finding(_scholar("Bob", ["Alice"]))
        # School 2: Carol ↔ Dave
        g.add_finding(_scholar("Carol", ["Dave"]))
        g.add_finding(_scholar("Dave", ["Carol"]))
        schools = g.detect_schools()
        assert len(schools) == 2

    def test_detect_schools_single_component(self):
        g = CitationGraph()
        g.add_finding(_scholar("Alice", ["Bob"]))
        g.add_finding(_scholar("Bob", ["Carol"]))
        g.add_finding(_scholar("Carol", ["Alice"]))
        schools = g.detect_schools()
        assert len(schools) == 1

    def test_check_single_school_critical(self):
        g = CitationGraph()
        g.add_finding(_scholar("Alice", ["Bob"]))
        g.add_finding(_scholar("Bob", ["Alice"]))
        anomaly = g.check_single_school()
        assert anomaly is not None
        assert anomaly.severity == Severity.CRITICAL
        assert anomaly.anomaly_type == AnomalyType.SCHOOL_GAP

    def test_check_multiple_schools_no_anomaly(self):
        g = CitationGraph()
        g.add_finding(_scholar("Alice", ["Bob"]))
        g.add_finding(_scholar("Bob", ["Alice"]))
        g.add_finding(_scholar("Carol", ["Dave"]))
        g.add_finding(_scholar("Dave", ["Carol"]))
        anomaly = g.check_single_school()
        assert anomaly is None

    def test_find_citation_islands(self):
        g = CitationGraph()
        # Eve is cited by Alice and Bob but never searched directly
        g.add_finding(_scholar("Alice", ["Eve"], query="search alice"))
        g.add_finding(_scholar("Bob", ["Eve"], query="search bob"))
        g.add_finding(Finding(
            name="Eve",
            finding_type=FindingType.SCHOLAR,
            source_query="",  # no direct search
            citations=[],
        ))
        islands = g.find_citation_islands(min_citations=2)
        assert len(islands) == 1
        assert islands[0]["name"] == "eve"
        assert islands[0]["in_citations"] == 2

    def test_investigation_priority_ranking(self):
        g = CitationGraph()
        g.add_finding(_scholar("Alice", ["Eve", "Frank"], query="search"))
        g.add_finding(_scholar("Bob", ["Eve"], query="search"))
        g.add_finding(_scholar("Eve", [], query="search eve"))
        rankings = g.investigation_priority_ranking()
        # Eve: in_citations=2, direct=1, priority=2/2=1.0
        # Frank: in_citations=1, direct=0, priority=1/1=1.0
        # Alice: in_citations=0, direct=1, priority=0/2=0.0
        eve_rank = next(r for r in rankings if r["name"] == "eve")
        assert eve_rank["priority"] == 1.0

    def test_generate_anomalies_includes_islands(self):
        g = CitationGraph()
        g.add_finding(_scholar("Alice", ["Eve"], query="search"))
        g.add_finding(_scholar("Bob", ["Eve"], query="search"))
        g.add_finding(Finding(
            name="Eve", finding_type=FindingType.SCHOLAR,
            source_query="", citations=[],
        ))
        anomalies = g.generate_anomalies()
        island_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.CITATION_ISLAND]
        assert len(island_anomalies) == 1

    def test_case_insensitive(self):
        g = CitationGraph()
        g.add_finding(_scholar("Alice", ["BOB"]))
        g.add_finding(_scholar("Carol", ["bob"]))
        # Both Alice and Carol cite Bob (case-insensitive)
        assert g.in_degree("bob") == 2

    def test_empty_graph(self):
        g = CitationGraph()
        assert g.node_count == 0
        assert g.detect_schools() == []
        assert g.find_citation_islands() == []
