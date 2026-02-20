"""Tests for citation graph analysis."""

from epistemix.citation_graph import CitationGraph
from epistemix.models import Finding, GapType


class TestCitationGraph:
    def test_build_from_findings(self, sample_findings):
        graph = CitationGraph()
        graph.build_from_findings(sample_findings)
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0

    def test_author_marked_investigated(self, sample_findings):
        graph = CitationGraph()
        graph.build_from_findings(sample_findings)
        assert graph.nodes["alice"].investigated is True
        assert graph.nodes["bob"].investigated is True

    def test_mentioned_entity_not_investigated(self):
        findings = [
            Finding(
                source="Paper", language="en",
                author="Alice",
                entities_mentioned=["Dave", "Eve"],
            )
        ]
        graph = CitationGraph()
        graph.build_from_findings(findings)
        assert graph.nodes["dave"].investigated is False

    def test_school_detection_mutual_citation(self):
        findings = [
            Finding(
                source="P1", language="en",
                author="Alice", entities_mentioned=["Bob"],
            ),
            Finding(
                source="P2", language="en",
                author="Bob", entities_mentioned=["Alice"],
            ),
        ]
        graph = CitationGraph()
        graph.build_from_findings(findings)
        schools = graph.detect_schools()
        assert len(schools) >= 1
        assert schools[0].size >= 2

    def test_no_school_without_mutual_citation(self):
        findings = [
            Finding(
                source="P1", language="en",
                author="Alice", entities_mentioned=["Bob"],
            ),
            Finding(
                source="P2", language="en",
                author="Carol", entities_mentioned=["Dave"],
            ),
        ]
        graph = CitationGraph()
        graph.build_from_findings(findings)
        schools = graph.detect_schools()
        # No mutual citations = no schools (of size >= 2)
        mutual_schools = [s for s in schools if s.size >= 2]
        assert len(mutual_schools) == 0

    def test_isolated_scholars(self):
        findings = [
            Finding(
                source="P1", language="en",
                author="Alice", entities_mentioned=["Zara"],
            ),
            Finding(
                source="P2", language="en",
                author="Bob", entities_mentioned=["Zara"],
            ),
            Finding(
                source="P3", language="en",
                author="Carol", entities_mentioned=["Zara"],
            ),
        ]
        graph = CitationGraph()
        graph.build_from_findings(findings)
        isolated = graph.detect_isolated_scholars()
        names = [n.name for n in isolated]
        assert "Zara" in names

    def test_priority_uninvestigated(self, sample_findings):
        graph = CitationGraph()
        graph.build_from_findings(sample_findings)
        priority = graph.get_priority_uninvestigated(3)
        # All prioritized should be uninvestigated
        for node in priority:
            assert not node.investigated

    def test_generate_anomalies_citation_island(self):
        findings = [
            Finding(
                source=f"P{i}", language="en",
                author=f"Author{i}", entities_mentioned=["Mystery Scholar"],
            )
            for i in range(5)
        ]
        graph = CitationGraph()
        graph.build_from_findings(findings)
        anomalies = graph.generate_anomalies()
        island_anomalies = [
            a for a in anomalies if a.gap_type == GapType.CITATION_ISLAND
        ]
        assert len(island_anomalies) >= 1

    def test_summary(self, sample_findings):
        graph = CitationGraph()
        graph.build_from_findings(sample_findings)
        summary = graph.summary()
        assert "total_nodes" in summary
        assert "total_edges" in summary

    def test_non_scholar_filtering(self):
        findings = [
            Finding(
                source="P1", language="en",
                author="Alice", entities_mentioned=["Amphipolis"],
            ),
        ]
        graph = CitationGraph()
        graph.register_non_scholars({"Amphipolis"})
        graph.build_from_findings(findings)
        assert "amphipolis" not in graph.nodes
