"""Tests for the core epistemic engine."""

from epistemix.core import (
    AuditEngine,
    DynamicInferenceEngine,
    DynamicPostulates,
    EpistemixEngine,
    ExpectationSatisfier,
    MultilingualQueryGenerator,
    calculate_coverage,
)
from epistemix.models import (
    Expectation,
    Finding,
    GapType,
    Severity,
)


class TestDynamicPostulates:
    def test_ingest_finding_new_author(self):
        post = DynamicPostulates("Greece", "test")
        f = Finding(
            source="Paper", language="en",
            author="Alice", institution="MIT",
        )
        new = post.ingest_finding(f)
        assert "Alice" in new
        assert "MIT" in new
        assert "alice" in post.entities
        assert post.entities["alice"].investigated is True

    def test_ingest_finding_tracks_language(self):
        post = DynamicPostulates("Greece", "test")
        f = Finding(source="Paper", language="el", author="Nikos")
        post.ingest_finding(f)
        assert "el" in post.languages_covered

    def test_ingest_finding_tracks_theory(self):
        post = DynamicPostulates("Greece", "test")
        f = Finding(
            source="Paper", language="en",
            theory_supported="Theory X",
        )
        post.ingest_finding(f)
        assert "Theory X" in post.theories

    def test_ingest_finding_deduplicates_entities(self):
        post = DynamicPostulates("Greece", "test")
        f1 = Finding(
            source="Paper1", language="en",
            author="Alice", entities_mentioned=["Bob"],
        )
        f2 = Finding(
            source="Paper2", language="en",
            author="Carol", entities_mentioned=["Bob"],
        )
        post.ingest_finding(f1)
        post.ingest_finding(f2)
        assert post.entities["bob"].times_mentioned >= 2

    def test_transliteration_normalization(self):
        post = DynamicPostulates("Greece", "test")
        f = Finding(
            source="Italian paper", language="it",
            entities_mentioned=["Efestione"],
        )
        post.ingest_finding(f)
        # "Efestione" should normalize to "hephaestion"
        assert "hephaestion" in post.entities

    def test_get_uninvestigated_scholars(self):
        post = DynamicPostulates("Greece", "test")
        f = Finding(
            source="Paper", language="en",
            author="Alice", entities_mentioned=["Bob", "Carol"],
        )
        post.ingest_finding(f)
        uninvestigated = post.get_uninvestigated_scholars()
        names = [e.name for e in uninvestigated]
        assert "Bob" in names
        assert "Carol" in names

    def test_snapshot(self):
        post = DynamicPostulates("Greece", "test")
        f = Finding(
            source="P", language="en", author="Alice",
            institution="MIT",
        )
        post.ingest_finding(f)
        snap = post.snapshot()
        assert snap["scholars"] >= 1
        assert "en" in snap["languages"]


class TestMultilingualQueryGenerator:
    def test_initial_queries_for_greece(self):
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        gen = MultilingualQueryGenerator(post)
        queries = gen.generate_initial_queries()
        languages = {q.language for q in queries}
        assert "en" in languages
        # Greece has Greek + foreign traditions
        assert len(queries) >= 3

    def test_gap_filling_queries(self):
        from epistemix.models import Anomaly
        post = DynamicPostulates("Greece", "test")
        gen = MultilingualQueryGenerator(post)
        anomalies = [
            Anomaly(
                description="Missing language",
                gap_type=GapType.LINGUISTIC,
                severity=Severity.HIGH,
            )
        ]
        queries = gen.generate_gap_filling_queries(anomalies)
        assert len(queries) >= 1


class TestDynamicInferenceEngine:
    def test_derive_expectations(self):
        post = DynamicPostulates("Greece", "test")
        post.theories.append("Theory X")
        post.institutions.add("MIT")
        inferrer = DynamicInferenceEngine(post)
        expectations = inferrer.derive(cycle=1)
        assert len(expectations) > 0
        gap_types = {e.gap_type for e in expectations}
        assert GapType.LINGUISTIC in gap_types
        assert GapType.THEORY_UNSOURCED in gap_types

    def test_entity_coverage_expectation(self):
        post = DynamicPostulates("Greece", "test")
        from epistemix.models import Entity, EntityType
        post.entities["bob"] = Entity(
            name="Bob", entity_type=EntityType.SCHOLAR,
            times_mentioned=3, investigated=False,
        )
        inferrer = DynamicInferenceEngine(post)
        expectations = inferrer.derive(cycle=1)
        entity_exps = [
            e for e in expectations
            if e.gap_type == GapType.ENTITY_UNRESEARCHED
        ]
        assert len(entity_exps) >= 1
        assert "Bob" in entity_exps[0].description


class TestExpectationSatisfier:
    def test_linguistic_satisfaction(self):
        post = DynamicPostulates("Greece", "test")
        expectations = [
            Expectation(
                description="Sources in 'en' language found",
                gap_type=GapType.LINGUISTIC,
                severity_if_unmet=Severity.HIGH,
            )
        ]
        findings = [Finding(source="Paper", language="en")]
        ExpectationSatisfier.satisfy(expectations, findings, post)
        assert expectations[0].met

    def test_source_type_satisfaction(self):
        post = DynamicPostulates("Greece", "test")
        expectations = [
            Expectation(
                description="Peer-reviewed sources found",
                gap_type=GapType.SOURCE_TYPE,
                severity_if_unmet=Severity.HIGH,
            )
        ]
        findings = [
            Finding(source="Paper", language="en", source_type="peer_reviewed")
        ]
        ExpectationSatisfier.satisfy(expectations, findings, post)
        assert expectations[0].met


class TestAuditEngine:
    def test_unmet_expectations_become_anomalies(self):
        post = DynamicPostulates("Greece", "test")
        expectations = [
            Expectation(
                description="Sources in 'el' language found",
                gap_type=GapType.LINGUISTIC,
                severity_if_unmet=Severity.HIGH,
                met=False,
            )
        ]
        auditor = AuditEngine(expectations, [], post)
        anomalies = auditor.run()
        assert len(anomalies) >= 1
        assert any(
            a.gap_type == GapType.LINGUISTIC for a in anomalies
        )


class TestCalculateCoverage:
    def test_all_met(self):
        expectations = [
            Expectation(
                description="A", gap_type=GapType.LINGUISTIC,
                severity_if_unmet=Severity.HIGH, met=True,
            ),
            Expectation(
                description="B", gap_type=GapType.TEMPORAL,
                severity_if_unmet=Severity.MEDIUM, met=True,
            ),
        ]
        score = calculate_coverage(expectations, [])
        assert score > 90

    def test_none_met(self):
        expectations = [
            Expectation(
                description="A", gap_type=GapType.LINGUISTIC,
                severity_if_unmet=Severity.HIGH, met=False,
            ),
        ]
        score = calculate_coverage(expectations, [])
        assert score == 0.0

    def test_anomaly_penalty(self):
        from epistemix.models import Anomaly
        expectations = [
            Expectation(
                description="A", gap_type=GapType.LINGUISTIC,
                severity_if_unmet=Severity.HIGH, met=True,
            ),
        ]
        anomalies = [
            Anomaly(
                description="X", gap_type=GapType.LINGUISTIC,
                severity=Severity.HIGH,
            )
        ]
        score_with = calculate_coverage(expectations, anomalies)
        score_without = calculate_coverage(expectations, [])
        assert score_with < score_without


class TestEpistemixEngine:
    def test_initialize_generates_queries(self):
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        queries = engine.initialize()
        assert len(queries) >= 3

    def test_ingest_and_cycle(self, cycle_0_findings):
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        new = engine.ingest_findings(cycle_0_findings)
        assert len(new) > 0
        snapshot = engine.run_cycle()
        assert snapshot.cycle == 1
        assert snapshot.n_findings > 0

    def test_to_dict(self, cycle_0_findings):
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.ingest_findings(cycle_0_findings)
        engine.run_cycle()
        d = engine.to_dict()
        assert "coverage_history" in d
        assert "findings" in d
        assert "anomalies" in d

    def test_report_string(self, cycle_0_findings):
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.ingest_findings(cycle_0_findings)
        engine.run_cycle()
        report = engine.report()
        assert "EPISTEMIX AUDIT REPORT" in report
        assert "Coverage" in report
