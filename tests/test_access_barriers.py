"""Tests for access barrier data structures and registry."""

from epistemix.models import AccessTier, LanguageEcosystem
from epistemix.knowledge import LANGUAGE_ECOSYSTEMS, CROSS_LANGUAGE_STRATEGIES
from epistemix.meta_axioms import (
    MA_08_ACCESS, META_AXIOMS, META_AXIOM_BY_ID,
    generate_postulate_descriptions,
)


class TestLanguageEcosystemRegistry:
    def test_chinese_ecosystem_exists(self):
        eco = LANGUAGE_ECOSYSTEMS["zh"]
        assert eco.language == "zh"
        assert eco.access_tier == AccessTier.WALLED_GARDEN
        assert "CNKI" in eco.gated_databases
        assert eco.estimated_gated_share == 0.70
        assert eco.query_style == "phrasal"
        assert eco.script == "cjk"

    def test_arabic_ecosystem_exists(self):
        eco = LANGUAGE_ECOSYSTEMS["ar"]
        assert eco.language == "ar"
        assert eco.access_tier == AccessTier.PARTIAL_ACCESS
        assert "Al-Manhal" in eco.gated_databases
        assert eco.estimated_gated_share == 0.35
        assert eco.query_style == "morphological"
        assert eco.script == "arabic"

    def test_japanese_ecosystem_exists(self):
        eco = LANGUAGE_ECOSYSTEMS["ja"]
        assert eco.language == "ja"
        assert eco.access_tier == AccessTier.PARTIAL_ACCESS
        assert "CiNii" in eco.gated_databases
        assert eco.query_style == "phrasal"
        assert eco.script == "cjk"

    def test_korean_ecosystem_exists(self):
        eco = LANGUAGE_ECOSYSTEMS["ko"]
        assert eco.language == "ko"
        assert eco.access_tier == AccessTier.PARTIAL_ACCESS
        assert "RISS" in eco.gated_databases
        assert eco.query_style == "phrasal"
        assert eco.script == "hangul"

    def test_all_ecosystems_are_frozen(self):
        for lang, eco in LANGUAGE_ECOSYSTEMS.items():
            try:
                eco.language = "xx"
                assert False, f"Ecosystem for {lang} should be frozen"
            except AttributeError:
                pass

    def test_ecosystem_count(self):
        assert len(LANGUAGE_ECOSYSTEMS) == 4


class TestCrossLanguageStrategies:
    def test_chinese_has_english_strategy(self):
        strategies = CROSS_LANGUAGE_STRATEGIES["zh"]
        langs = [s[0] for s in strategies]
        assert "en" in langs

    def test_arabic_has_english_and_french(self):
        strategies = CROSS_LANGUAGE_STRATEGIES["ar"]
        langs = [s[0] for s in strategies]
        assert "en" in langs
        assert "fr" in langs

    def test_strategy_templates_have_topic_placeholder(self):
        for lang, strategies in CROSS_LANGUAGE_STRATEGIES.items():
            for target_lang, template in strategies:
                assert "{topic}" in template, (
                    f"Strategy {lang}→{target_lang} missing {{topic}} placeholder"
                )

    def test_all_ecosystems_have_strategies(self):
        for lang in LANGUAGE_ECOSYSTEMS:
            assert lang in CROSS_LANGUAGE_STRATEGIES, (
                f"Missing cross-language strategy for {lang}"
            )


class TestMA08AccessBarriers:
    def test_axiom_id(self):
        assert MA_08_ACCESS.id == "MA-08"

    def test_axiom_name(self):
        assert MA_08_ACCESS.name == "Access Barriers"

    def test_axiom_has_postulate_templates(self):
        assert len(MA_08_ACCESS.postulate_templates) >= 3

    def test_axiom_in_meta_axioms_tuple(self):
        assert MA_08_ACCESS in META_AXIOMS
        assert len(META_AXIOMS) == 8

    def test_axiom_in_lookup_dict(self):
        assert "MA-08" in META_AXIOM_BY_ID
        assert META_AXIOM_BY_ID["MA-08"] is MA_08_ACCESS


# ============================================================
# Task 6: Engine integration tests
# ============================================================

from epistemix.core import (
    EpistemixEngine,
    DynamicInferenceEngine,
    DynamicPostulates,
    calculate_coverage,
)
from epistemix.models import (
    CoverageBreakdown, Expectation, Finding,
    GapType, NegativePostulate, Severity,
)
from epistemix.connector import MockConnector


class TestAccessBarrierInference:
    def test_china_topic_generates_barrier_expectations(self):
        postulates = DynamicPostulates("China", "SARS-CoV-2 origins", "virology")
        inferrer = DynamicInferenceEngine(postulates)
        expectations = inferrer.derive(1)
        barrier_exps = [
            e for e in expectations
            if e.gap_type == GapType.ACCESS_BARRIER
        ]
        assert len(barrier_exps) >= 1
        assert any("zh" in e.description.lower() or "chinese" in e.description.lower()
                    for e in barrier_exps)

    def test_greece_topic_no_barrier_expectations(self):
        postulates = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        inferrer = DynamicInferenceEngine(postulates)
        expectations = inferrer.derive(1)
        barrier_exps = [
            e for e in expectations
            if e.gap_type == GapType.ACCESS_BARRIER
        ]
        assert len(barrier_exps) == 0

    def test_egypt_topic_generates_arabic_barrier(self):
        postulates = DynamicPostulates("Egypt", "pyramid construction", "archaeology")
        inferrer = DynamicInferenceEngine(postulates)
        expectations = inferrer.derive(1)
        barrier_exps = [
            e for e in expectations
            if e.gap_type == GapType.ACCESS_BARRIER
        ]
        assert len(barrier_exps) >= 1


class TestCoverageBreakdownCalculation:
    def test_no_barriers_returns_breakdown_with_zero_unreachable(self):
        expectations = [
            Expectation("Sources in 'en'", GapType.LINGUISTIC, Severity.HIGH, met=True),
            Expectation("Sources in 'el'", GapType.LINGUISTIC, Severity.HIGH, met=False),
        ]
        anomalies = []
        result = calculate_coverage(expectations, anomalies)
        assert isinstance(result, CoverageBreakdown)
        assert result.estimated_unreachable == 0.0
        assert result.gated_expectations_count == 0

    def test_barrier_expectations_excluded_from_accessible_score(self):
        expectations = [
            Expectation("Sources in 'en'", GapType.LINGUISTIC, Severity.HIGH, met=True),
            Expectation("CNKI gated (zh, 70% gated)", GapType.ACCESS_BARRIER, Severity.MEDIUM, met=False),
        ]
        anomalies = []
        result = calculate_coverage(expectations, anomalies)
        assert result.accessible_score > 0
        assert result.gated_expectations_count == 1
        assert result.gated_expectations_met == 0

    def test_estimated_unreachable_reflects_gated_share(self):
        expectations = [
            Expectation("Sources in 'en'", GapType.LINGUISTIC, Severity.HIGH, met=True),
            Expectation("Chinese sources behind CNKI (zh, 70% gated)", GapType.ACCESS_BARRIER, Severity.MEDIUM, met=False),
        ]
        anomalies = []
        result = calculate_coverage(expectations, anomalies)
        assert result.estimated_unreachable > 0

    def test_backward_compatible_snapshot_coverage(self):
        """CycleSnapshot.coverage_score should still be a float (accessible_score)."""
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        snapshot = engine.run_cycle()
        assert isinstance(snapshot.coverage_score, float)


class TestNegativePostulateAccessBarrier:
    def test_access_barrier_reason_for_chinese_query(self):
        neg = NegativePostulate(
            query_text="\u75c5\u6bd2\u8d77\u6e90\u7814\u7a76",
            language="zh",
            possible_reason="access_barrier",
            reformulation="Chinese research on virus origins",
            detected_at_cycle=1,
        )
        assert neg.possible_reason == "access_barrier"
        assert neg.language == "zh"
        assert "Chinese" in neg.reformulation or "research" in neg.reformulation


# ============================================================
# Task 7: SARS-CoV-2 integration tests
# ============================================================

class TestSARSCoV2Integration:
    """Full pipeline test with SARS-CoV-2 topic exercising access barriers."""

    def test_china_audit_produces_barrier_anomalies(
        self, sars_connector, sars_findings,
    ):
        engine = EpistemixEngine("China", "SARS-CoV-2 origins", "virology")
        engine.initialize()
        engine.ingest_findings(sars_findings)
        snapshot = engine.run_cycle(sars_connector)

        barrier_exps = [
            e for e in engine.all_expectations
            if e.gap_type == GapType.ACCESS_BARRIER
        ]
        assert len(barrier_exps) >= 1
        assert 0 <= snapshot.coverage_score <= 100

    def test_china_audit_coverage_breakdown(
        self, sars_connector, sars_findings,
    ):
        engine = EpistemixEngine("China", "SARS-CoV-2 origins", "virology")
        engine.initialize()
        engine.ingest_findings(sars_findings)
        engine.run_cycle(sars_connector)

        result = engine.to_dict()
        breakdown = result.get("coverage_breakdown")
        assert breakdown is not None
        assert "accessible_score" in breakdown
        assert "estimated_unreachable" in breakdown
        assert breakdown["estimated_unreachable"] > 0

    def test_greece_audit_no_barrier_in_breakdown(self):
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.run_cycle()

        result = engine.to_dict()
        breakdown = result.get("coverage_breakdown")
        assert breakdown is not None
        assert breakdown["estimated_unreachable"] == 0.0
        assert breakdown["gated_expectations_count"] == 0
