"""Tests for the core epistemic engine."""

from epistemix.core import (
    AuditEngine,
    DECAY_RATES,
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
    NegativePostulate,
    Severity,
    WeightedPostulate,
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
        result = calculate_coverage(expectations, [])
        assert result.accessible_score > 90

    def test_none_met(self):
        expectations = [
            Expectation(
                description="A", gap_type=GapType.LINGUISTIC,
                severity_if_unmet=Severity.HIGH, met=False,
            ),
        ]
        result = calculate_coverage(expectations, [])
        assert result.accessible_score == 0.0

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
        result_with = calculate_coverage(expectations, anomalies)
        result_without = calculate_coverage(expectations, [])
        assert result_with.accessible_score < result_without.accessible_score


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


# ============================================================
# v3 Phase 1: Weighted Postulates
# ============================================================

class TestWeightedPostulates:
    def test_ingestion_creates_weighted_postulates(self):
        """Ingesting a finding should create weighted postulates."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        f = Finding(
            source="Paper", language="en",
            author="Alice", institution="MIT",
            theory_supported="Theory X",
            entities_mentioned=["Bob"],
            cycle=1,
        )
        post.ingest_finding(f)
        assert len(post.weighted_postulates) > 0
        # Alice, MIT, Theory X, Bob should all have entries
        assert "alice" in post.weighted_postulates
        assert "mit" in post.weighted_postulates
        assert "theory x" in post.weighted_postulates

    def test_confidence_increases_with_sources(self):
        """More sources = higher confidence."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        f1 = Finding(
            source="Paper 1", language="en",
            author="Alice", cycle=1,
        )
        post.ingest_finding(f1)
        conf_1 = post.weighted_postulates["alice"].confidence

        f2 = Finding(
            source="Paper 2", language="en",
            entities_mentioned=["Alice"], cycle=1,
        )
        post.ingest_finding(f2)
        conf_2 = post.weighted_postulates["alice"].confidence

        assert conf_2 > conf_1

    def test_language_spread_boosts_confidence(self):
        """Same entity in multiple languages = higher confidence."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        f1 = Finding(
            source="Paper EN", language="en",
            author="Peristeri", cycle=1,
        )
        f2 = Finding(
            source="Paper EL", language="el",
            author="Peristeri", cycle=2,
        )
        post.ingest_finding(f1)
        conf_en_only = post.weighted_postulates["peristeri"].confidence

        post.ingest_finding(f2)
        conf_multilingual = post.weighted_postulates["peristeri"].confidence

        assert conf_multilingual > conf_en_only
        assert post.weighted_postulates["peristeri"].language_spread == 2

    def test_decay_rate_from_discipline(self):
        """Decay rate should match the discipline."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        f = Finding(
            source="Paper", language="en",
            author="Alice", cycle=1,
        )
        post.ingest_finding(f)
        wp = post.weighted_postulates["alice"]
        assert wp.decay_rate == DECAY_RATES["archaeology"]

    def test_snapshot_includes_weighted_postulates(self):
        """Snapshot should include v3 fields."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        f = Finding(
            source="Paper", language="en",
            author="Alice", cycle=1,
        )
        post.ingest_finding(f)
        snap = post.snapshot()
        assert "weighted_postulates" in snap
        assert snap["weighted_postulates"] > 0
        assert "avg_confidence" in snap
        assert snap["avg_confidence"] > 0

    def test_describe_shows_confidence(self):
        """Describe should mention weighted postulates."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        f = Finding(
            source="Paper", language="en",
            author="Alice", cycle=1,
        )
        post.ingest_finding(f)
        desc = post.describe()
        assert "Weighted postulates" in desc


class TestConfidenceQueryGeneration:
    def test_low_confidence_generates_verify_queries(self):
        """Postulates with low confidence should get verification queries."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        # Manually set a low-confidence postulate
        post.weighted_postulates["obscure scholar"] = WeightedPostulate(
            description="Obscure Scholar",
            confidence=0.15,
            source_count=1,
        )
        gen = MultilingualQueryGenerator(post)
        queries = gen.generate_confidence_queries()
        verify_queries = [
            q for q in queries
            if "Verify" in q.rationale or "verify" in q.rationale.lower()
        ]
        assert len(verify_queries) >= 1

    def test_high_confidence_mono_generates_deepen_queries(self):
        """High-confidence postulates with one language get deepening queries."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        post.weighted_postulates["well known"] = WeightedPostulate(
            description="Well Known",
            confidence=0.85,
            source_count=5,
            language_spread=1,
        )
        gen = MultilingualQueryGenerator(post)
        queries = gen.generate_confidence_queries()
        deepen_queries = [
            q for q in queries
            if "Deepen" in q.rationale or "deepen" in q.rationale.lower()
        ]
        assert len(deepen_queries) >= 1

    def test_no_queries_for_standard_confidence(self):
        """Standard-confidence postulates don't generate extra queries."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        post.weighted_postulates["normal"] = WeightedPostulate(
            description="Normal",
            confidence=0.5,
            source_count=2,
            language_spread=2,
        )
        gen = MultilingualQueryGenerator(post)
        queries = gen.generate_confidence_queries()
        assert len(queries) == 0


# ============================================================
# v3 Phase 2: Negative Postulates
# ============================================================

class TestNegativePostulates:
    def test_register_negative_postulate(self):
        """DynamicPostulates should accept negative postulates."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        neg = NegativePostulate(
            query_text="test query",
            language="de",
            expected_by="MA-01",
            possible_reason="wrong_terminology",
        )
        post.register_negative_postulate(neg)
        assert len(post.negative_postulates) == 1
        assert post.negative_postulates[0].language == "de"

    def test_negative_postulates_in_snapshot(self):
        """Snapshot should count negative postulates."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        neg = NegativePostulate(query_text="q", language="de")
        post.register_negative_postulate(neg)
        snap = post.snapshot()
        assert snap["negative_postulates"] == 1

    def test_negative_postulate_generates_reformulation_query(self):
        """Negative postulates with reformulations generate gap-filling queries."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        neg = NegativePostulate(
            query_text="old query",
            language="de",
            reformulation="better query in German",
        )
        post.register_negative_postulate(neg)

        gen = MultilingualQueryGenerator(post)
        queries = gen.generate_gap_filling_queries([])
        reformulated = [
            q for q in queries if "Reformulation" in q.rationale
        ]
        assert len(reformulated) >= 1
        assert reformulated[0].query == "better query in German"
        assert reformulated[0].language == "de"


# ============================================================
# v3 Phase 7: Temporal Decay
# ============================================================

class TestTemporalDecay:
    def test_decay_applied_in_run_cycle(self, cycle_0_findings):
        """run_cycle should apply temporal decay to weighted postulates."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.ingest_findings(cycle_0_findings)

        # First cycle: postulates are created
        snap1 = engine.run_cycle()
        assert snap1.weighted_postulates_count > 0

        # Run 3 more cycles without new findings → confidence decays
        for _ in range(3):
            engine.run_cycle()

        final_snap = engine.cycle_history[-1]
        # Average confidence should decrease (decay without confirmation)
        assert final_snap.avg_confidence <= snap1.avg_confidence

    def test_confirmation_resets_decay(self):
        """Re-confirming a postulate should reset its last_confirmed_cycle."""
        post = DynamicPostulates("Greece", "test", "archaeology")
        f1 = Finding(
            source="Paper 1", language="en",
            author="Alice", cycle=1,
        )
        post.ingest_finding(f1)
        wp = post.weighted_postulates["alice"]
        assert wp.last_confirmed_cycle == 1

        f2 = Finding(
            source="Paper 2", language="el",
            entities_mentioned=["Alice"], cycle=5,
        )
        post.ingest_finding(f2)
        assert wp.last_confirmed_cycle == 5


# ============================================================
# v3: Engine serialization includes v3 data
# ============================================================

class TestEngineV3Serialization:
    def test_to_dict_includes_weighted_postulates(self, cycle_0_findings):
        """to_dict should include weighted_postulates and negative_postulates."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.ingest_findings(cycle_0_findings)
        engine.run_cycle()
        d = engine.to_dict()
        assert "weighted_postulates" in d
        assert isinstance(d["weighted_postulates"], list)
        assert len(d["weighted_postulates"]) > 0
        assert "negative_postulates" in d
        assert isinstance(d["negative_postulates"], list)

    def test_cycle_snapshot_has_v3_fields(self, cycle_0_findings):
        """CycleSnapshot should include weighted postulate metrics."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.ingest_findings(cycle_0_findings)
        snap = engine.run_cycle()
        assert snap.weighted_postulates_count > 0
        assert snap.avg_confidence > 0
        d = snap.to_dict()
        assert "weighted_postulates" in d
        assert "avg_confidence" in d
