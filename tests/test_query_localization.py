"""Tests for query_localization module."""

from epistemix.query_localization import (
    localize_query,
    localize_query_via_llm,
    ARABIC_ACADEMIC_TERMS,
    ARABIC_TOPIC_TERMS,
    CHINESE_ACADEMIC_TERMS,
    CHINESE_TOPIC_TERMS,
    JAPANESE_ACADEMIC_TERMS,
    JAPANESE_TOPIC_TERMS,
    KOREAN_ACADEMIC_TERMS,
    KOREAN_TOPIC_TERMS,
)


class TestArabicLocalization:
    def test_arabic_queries_generated(self):
        queries = localize_query("archaeology", "ar", "archaeology")
        assert len(queries) > 0
        # Should contain Arabic script characters
        assert any("\u0627" in q or "\u0628" in q for q in queries), (
            "Arabic queries should contain Arabic script"
        )

    def test_arabic_has_morphological_variants(self):
        queries = localize_query("archaeology", "ar", "archaeology")
        # Multiple queries due to morphological expansion
        assert len(queries) >= 2

    def test_arabic_academic_terms_exist(self):
        assert len(ARABIC_ACADEMIC_TERMS) > 0
        # Should have research-related Arabic terms
        assert any("\u0628\u062d\u062b" in term for term in ARABIC_ACADEMIC_TERMS), (
            "Should include research/bahth terms"
        )


class TestChineseLocalization:
    def test_chinese_queries_generated(self):
        queries = localize_query("archaeology", "zh", "archaeology")
        assert len(queries) > 0

    def test_chinese_has_phrasal_compounds(self):
        queries = localize_query("archaeology", "zh", "archaeology")
        # Chinese queries should contain CJK characters
        assert any(
            any("\u4e00" <= ch <= "\u9fff" for ch in q)
            for q in queries
        ), "Chinese queries should contain CJK characters"

    def test_chinese_academic_terms_exist(self):
        assert len(CHINESE_ACADEMIC_TERMS) > 0
        # Should include research term
        assert any("\u7814\u7a76" in term for term in CHINESE_ACADEMIC_TERMS), (
            "Should include \u7814\u7a76 (research)"
        )


class TestJapaneseLocalization:
    def test_japanese_queries_generated(self):
        queries = localize_query("archaeology", "ja", "archaeology")
        assert len(queries) > 0

    def test_japanese_has_kanji(self):
        queries = localize_query("archaeology", "ja", "archaeology")
        assert any(
            any("\u4e00" <= ch <= "\u9fff" or "\u30a0" <= ch <= "\u30ff" for ch in q)
            for q in queries
        ), "Japanese queries should contain kanji or katakana"

    def test_japanese_academic_terms_exist(self):
        assert len(JAPANESE_ACADEMIC_TERMS) > 0


class TestKoreanLocalization:
    def test_korean_queries_generated(self):
        queries = localize_query("archaeology", "ko", "archaeology")
        assert len(queries) > 0

    def test_korean_has_hangul(self):
        queries = localize_query("archaeology", "ko", "archaeology")
        assert any(
            any("\uac00" <= ch <= "\ud7a3" for ch in q)
            for q in queries
        ), "Korean queries should contain Hangul characters"

    def test_korean_academic_terms_exist(self):
        assert len(KOREAN_ACADEMIC_TERMS) > 0


class TestLocalizeQueryGeneral:
    def test_unsupported_language_returns_empty(self):
        queries = localize_query("archaeology", "sv", "archaeology")
        assert queries == []

    def test_returns_list_of_strings(self):
        for lang in ("ar", "zh", "ja", "ko"):
            queries = localize_query("test topic", lang, "science")
            assert isinstance(queries, list)
            for q in queries:
                assert isinstance(q, str)

    def test_topic_influences_output(self):
        q1 = localize_query("archaeology", "zh", "archaeology")
        q2 = localize_query("virology", "zh", "science")
        # Different topics should produce different queries
        assert set(q1) != set(q2)


class TestLLMFallback:
    def test_llm_fallback_with_mock_connector(self):
        from epistemix.connector import MockConnector
        connector = MockConnector()
        connector.register_localized_queries("ar", [
            "\u0628\u062d\u062b \u0623\u062b\u0631\u064a",
            "\u062f\u0631\u0627\u0633\u0629 \u0639\u0644\u0645 \u0627\u0644\u0622\u062b\u0627\u0631",
        ])
        queries = localize_query_via_llm(
            "archaeology", "ar", "archaeology", connector,
        )
        assert len(queries) == 2
        assert "\u0628\u062d\u062b \u0623\u062b\u0631\u064a" in queries
