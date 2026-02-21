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
