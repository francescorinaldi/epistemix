"""Amphipolis 4-cycle simulation — the reference scenario.

Simulates a realistic epistemic audit of the Amphipolis tomb,
using the founder's rich simulation data converted to pytest.
Tests coverage progression, entity discovery, anomaly detection,
and multi-agent divergence.
"""

from epistemix.core import DynamicPostulates, EpistemixEngine
from epistemix.citation_graph import CitationGraph
from epistemix.disciplines import DisciplineAnalyzer
from epistemix.multi_agent import (
    AgentInstitutional,
    AgentTheoretical,
    Arbiter,
    MultiAgentSystem,
)
from epistemix.models import GapType


class TestAmphipolisSimulation:
    """Tests using the Amphipolis reference scenario."""

    def test_cycle_0_discovers_key_entities(self, cycle_0_findings):
        """First cycle should discover major researchers."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        new_entities = engine.ingest_findings(cycle_0_findings)

        # Should discover key figures
        entity_names_lower = [e.lower() for e in new_entities]
        assert any("peristeri" in n for n in entity_names_lower)
        assert any("chugg" in n for n in entity_names_lower)

    def test_cycle_0_tracks_theories(self, cycle_0_findings):
        """First cycle should identify major theories."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.ingest_findings(cycle_0_findings)
        engine.run_cycle()

        theories = engine.postulates.theories
        assert any("Hephaestion" in t for t in theories)
        assert any("Olympias" in t for t in theories)

    def test_coverage_progression(
        self, cycle_0_findings, cycle_1_findings,
        cycle_2_findings, cycle_3_findings,
    ):
        """Coverage should improve across cycles."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()

        cycles = [
            cycle_0_findings, cycle_1_findings,
            cycle_2_findings, cycle_3_findings,
        ]
        for findings in cycles:
            engine.ingest_findings(findings)
            engine.run_cycle()

        # Should have 4 snapshots
        assert len(engine.cycle_history) == 4

        # More expectations should be met over time
        met_counts = [s.n_expectations_met for s in engine.cycle_history]
        assert met_counts[-1] >= met_counts[0]

    def test_multilingual_coverage(
        self, cycle_0_findings, cycle_1_findings,
    ):
        """Finds should span multiple languages."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.ingest_findings(cycle_0_findings)
        engine.ingest_findings(cycle_1_findings)
        engine.run_cycle()

        languages = engine.postulates.languages_covered
        assert "en" in languages
        assert "el" in languages
        # Cycle 1 adds Italian and French
        assert "it" in languages or "fr" in languages

    def test_transliteration_normalization(self, cycle_1_findings):
        """Efestione (Italian) should normalize to Hephaestion."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.ingest_findings(cycle_1_findings)

        # Check if Mavrogiannis's mentions of "Anfipoli" are normalized
        entities = engine.postulates.entities
        # "Efestione" mentioned in cycle_1 should normalize
        assert "hephaestion" in entities or any(
            "hephaestion" in k for k in entities
        )

    def test_discipline_gap_detection(self, all_findings):
        """Should detect missing specialist disciplines."""
        analyzer = DisciplineAnalyzer("archaeology")
        analyzer.ingest_findings(all_findings)
        anomalies = analyzer.generate_anomalies()

        # With our data, some disciplines should be missing
        gap_types = [a.gap_type for a in anomalies]
        assert GapType.DISCIPLINE_GAP in gap_types

    def test_citation_graph_structure(self, all_findings):
        """Citation graph should reflect the research network."""
        graph = CitationGraph()
        graph.build_from_findings(all_findings)

        assert len(graph.nodes) > 5
        assert len(graph.edges) > 0

        # Key researchers should be investigated
        if "katerina peristeri" in graph.nodes:
            assert graph.nodes["katerina peristeri"].investigated

    def test_serialization(
        self, cycle_0_findings, cycle_1_findings,
    ):
        """Engine state should serialize cleanly."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.ingest_findings(cycle_0_findings)
        engine.run_cycle()
        engine.ingest_findings(cycle_1_findings)
        engine.run_cycle()

        d = engine.to_dict()
        assert d["cycle"] == 2
        assert len(d["coverage_history"]) == 2
        assert len(d["findings"]) > 0
        assert isinstance(d["coverage_percentage"], float)


class TestAmphipolisMultiAgent:
    """Multi-agent tests with Amphipolis data."""

    def test_dual_agent_produces_results(self, all_findings):
        """Both agents should produce meaningful reports."""
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)

        alpha = AgentInstitutional(post)
        beta = AgentTheoretical(post)

        report_a = alpha.audit(all_findings)
        report_b = beta.audit(all_findings)

        assert len(report_a.expectations) > 0
        assert len(report_b.expectations) > 0
        assert report_a.coverage_score >= 0
        assert report_b.coverage_score >= 0

    def test_agents_find_different_anomalies(self, all_findings):
        """Agents with different focuses should find different issues."""
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)

        alpha = AgentInstitutional(post)
        beta = AgentTheoretical(post)

        report_a = alpha.audit(all_findings)
        report_b = beta.audit(all_findings)

        # They should have different gap types in their anomalies
        alpha_types = {a.gap_type for a in report_a.anomalies}
        beta_types = {a.gap_type for a in report_b.anomalies}
        # At least one type should differ
        assert alpha_types != beta_types or (
            len(report_a.anomalies) == 0 and len(report_b.anomalies) == 0
        )

    def test_arbiter_finds_known_unknowns(self, all_findings):
        """Arbiter should identify discrepancies between agents."""
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)

        system = MultiAgentSystem(post)
        result = system.run(all_findings)

        assert "combined" in result
        assert "known_unknowns" in result["combined"]
        assert result["combined"]["total_anomalies"] >= 0

    def test_multi_agent_serialization(self, all_findings):
        """Multi-agent result should serialize for database."""
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)

        system = MultiAgentSystem(post)
        result = system.run(all_findings)

        # Check structure matches what worker writes to DB
        assert "alpha" in result
        assert "beta" in result
        assert "coverage" in result["alpha"]
        assert "coverage" in result["beta"]
        assert "blindness_gap" in result["combined"]
