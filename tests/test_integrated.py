"""Full integration test — runs the complete pipeline."""

from epistemix.connector import MockConnector
from epistemix.core import EpistemixEngine
from epistemix.citation_graph import CitationGraph
from epistemix.content_analysis import ContentAnalysisEngine
from epistemix.disciplines import DisciplineAnalyzer
from epistemix.multi_agent import MultiAgentSystem
from epistemix.models import Finding


class TestFullPipeline:
    def test_engine_multi_cycle(
        self, cycle_0_findings, cycle_1_findings
    ):
        """Test 2-cycle engine run with manual finding injection."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()

        # Cycle 1
        engine.ingest_findings(cycle_0_findings)
        snap1 = engine.run_cycle()
        assert snap1.cycle == 1
        assert snap1.n_findings > 0

        # Cycle 2
        engine.ingest_findings(cycle_1_findings)
        snap2 = engine.run_cycle()
        assert snap2.cycle == 2
        assert snap2.n_findings > snap1.n_findings

    def test_coverage_increases_with_more_data(
        self, cycle_0_findings, cycle_1_findings
    ):
        """Coverage should generally improve with more diverse findings."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()

        engine.ingest_findings(cycle_0_findings)
        snap1 = engine.run_cycle()

        engine.ingest_findings(cycle_1_findings)
        snap2 = engine.run_cycle()

        # More data = more expectations met
        assert snap2.n_expectations_met >= snap1.n_expectations_met

    def test_auxiliary_analyses(self, all_findings):
        """Citation graph, disciplines, content analysis all work."""
        # Citation graph
        graph = CitationGraph()
        graph.build_from_findings(all_findings)
        summary = graph.summary()
        assert summary["total_nodes"] > 0

        # Disciplines
        analyzer = DisciplineAnalyzer("archaeology")
        analyzer.ingest_findings(all_findings)
        disc_summary = analyzer.coverage_summary()
        assert len(disc_summary["relevant_disciplines"]) > 0

        # Content analysis
        content = ContentAnalysisEngine()
        anomalies = content.generate_all_anomalies()
        assert isinstance(anomalies, list)

    def test_multi_agent_with_real_data(self, all_findings):
        """Multi-agent system produces valid output."""
        from epistemix.core import DynamicPostulates

        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)

        system = MultiAgentSystem(post)
        result = system.run(all_findings)

        assert "alpha" in result
        assert "beta" in result
        assert "combined" in result
        assert result["combined"]["total_anomalies"] >= 0
        assert result["combined"]["known_unknowns"] >= 0

    def test_full_end_to_end(
        self, cycle_0_findings, cycle_1_findings,
        cycle_2_findings, cycle_3_findings,
    ):
        """Full 4-cycle audit with all auxiliary analyses."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()

        all_cycles = [
            cycle_0_findings, cycle_1_findings,
            cycle_2_findings, cycle_3_findings,
        ]
        for cycle_findings in all_cycles:
            engine.ingest_findings(cycle_findings)
            engine.run_cycle()

        # Should have 4 cycle snapshots
        assert len(engine.cycle_history) == 4

        # Coverage should be meaningful
        final = engine.cycle_history[-1]
        assert final.coverage_score > 0

        # Engine should be serializable
        d = engine.to_dict()
        assert d["cycle"] == 4
        assert len(d["coverage_history"]) == 4
        assert len(d["findings"]) > 0

        # Report should be generated
        report = engine.report()
        assert "Evolution" in report  # Multi-cycle shows evolution

    def test_with_mock_connector(self):
        """Test using MockConnector for query execution."""
        connector = MockConnector()
        connector.register_findings("amphipolis", [
            Finding(
                source="Paper A", language="en",
                author="Alice", institution="MIT",
                theory_supported="Theory X",
                source_type="peer_reviewed", year=2024,
            ),
        ])
        connector.register_findings("tomb", [
            Finding(
                source="Paper B", language="el",
                author="Nikos", institution="AUTH",
                theory_supported="Theory Y",
                source_type="institutional", year=2023,
            ),
        ])

        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        queries = engine.initialize()

        # Execute queries through connector
        findings = connector.execute_batch(queries)
        assert len(findings) > 0

        engine.ingest_findings(findings)
        snapshot = engine.run_cycle()
        assert snapshot.n_findings > 0
        assert snapshot.coverage_score >= 0
