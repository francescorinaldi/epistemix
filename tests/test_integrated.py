"""Full integration test — runs the complete pipeline."""

from epistemix.connector import MockConnector
from epistemix.core import EpistemixEngine
from epistemix.content_analysis import ContentAnalysisEngine
from epistemix.disciplines import DisciplineAnalyzer
from epistemix.multi_agent import MultiAgentSystem
from epistemix.models import Finding, RelationType, SemanticRelation


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
        """Semantic graph, disciplines, content analysis all work."""
        # Semantic graph (replaces citation graph)
        from epistemix.semantic_graph import SemanticGraph
        graph = SemanticGraph()
        assert graph.summary()["total_nodes"] == 0  # empty until relations added

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

    def test_v3_weighted_postulates_across_cycles(
        self, cycle_0_findings, cycle_1_findings,
        cycle_2_findings, cycle_3_findings,
    ):
        """v3: Weighted postulates accumulate and confidence grows."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()

        all_cycles = [
            cycle_0_findings, cycle_1_findings,
            cycle_2_findings, cycle_3_findings,
        ]
        for cycle_findings in all_cycles:
            engine.ingest_findings(cycle_findings)
            engine.run_cycle()

        # Should have weighted postulates created from all findings
        wps = engine.postulates.weighted_postulates
        assert len(wps) > 0

        # Peristeri appears in many findings → high confidence
        peristeri_key = "katerina peristeri"
        assert peristeri_key in wps
        assert wps[peristeri_key].confidence > 0.3
        assert wps[peristeri_key].source_count >= 2

        # to_dict should include v3 data
        d = engine.to_dict()
        assert len(d["weighted_postulates"]) > 0
        assert any(
            wp["description"] == "Katerina Peristeri"
            for wp in d["weighted_postulates"]
        )

    def test_v3_cycle_snapshots_have_confidence(
        self, cycle_0_findings, cycle_1_findings,
    ):
        """v3: CycleSnapshot includes weighted postulate metrics."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()

        engine.ingest_findings(cycle_0_findings)
        snap1 = engine.run_cycle()
        assert snap1.weighted_postulates_count > 0
        assert snap1.avg_confidence > 0

        engine.ingest_findings(cycle_1_findings)
        snap2 = engine.run_cycle()
        # More findings → more postulates
        assert snap2.weighted_postulates_count >= snap1.weighted_postulates_count

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


class TestSemanticGraphIntegration:
    def test_run_cycle_with_connector_builds_graph(self):
        connector = MockConnector()
        connector.register_findings("amphipolis", [
            Finding(
                source="Paper A", language="en",
                author="Alice", institution="MIT",
                source_type="peer_reviewed", year=2024,
            ),
        ])
        connector.register_relations([
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES, confidence=0.9,
                evidence="Alice cites Bob", language="en",
            ),
        ])

        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        queries = engine.initialize()
        findings = connector.execute_batch(queries)
        engine.ingest_findings(findings)
        snapshot = engine.run_cycle(connector=connector)

        assert snapshot.relations_count == 1
        assert len(engine.semantic_graph.relations) == 1

    def test_run_cycle_without_connector_still_works(self):
        """Backward compatibility: no connector = no graph analysis."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.ingest_findings([
            Finding(source="Paper", language="en", author="Alice",
                    source_type="peer_reviewed", year=2024),
        ])
        snapshot = engine.run_cycle()
        assert snapshot.relations_count == 0
