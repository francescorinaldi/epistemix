"""Localized query generation for non-Latin-script languages.

Generates culturally-aware search queries for Arabic, Chinese,
Japanese, and Korean. Each language has its own query style:
  - Arabic: morphological variants from triliteral roots
  - Chinese: phrasal compounds, simplified + traditional
  - Japanese: kanji + katakana
  - Korean: hangul compounds

Main entry point: localize_query(topic, language, discipline) -> list[str]
LLM fallback: localize_query_via_llm(topic, language, discipline, connector)

Zero external dependencies — all terms are embedded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from epistemix.connector import BaseConnector


# ============================================================
# ARABIC TERMS
# ============================================================

ARABIC_ACADEMIC_TERMS: list[str] = [
    "\u0628\u062d\u062b",       # bahth (research)
    "\u062f\u0631\u0627\u0633\u0629",     # dirasa (study)
    "\u0645\u0642\u0627\u0644\u0629",     # maqala (article)
    "\u0631\u0633\u0627\u0644\u0629",     # risala (thesis/dissertation)
    "\u0639\u0644\u0645\u064a",       # ilmi (scientific/academic)
    "\u0623\u0643\u0627\u062f\u064a\u0645\u064a",   # akadimi (academic)
    "\u0645\u062c\u0644\u0629",       # majalla (journal)
]

ARABIC_TOPIC_TERMS: dict[str, list[str]] = {
    "archaeology": [
        "\u0639\u0644\u0645 \u0627\u0644\u0622\u062b\u0627\u0631",     # ilm al-athar (archaeology)
        "\u0622\u062b\u0627\u0631",           # athar (antiquities)
        "\u062a\u0646\u0642\u064a\u0628",         # tanqib (excavation)
        "\u062d\u0641\u0631\u064a\u0627\u062a",       # hafriyat (excavations)
    ],
    "history": [
        "\u062a\u0627\u0631\u064a\u062e",         # tarikh (history)
        "\u062a\u0627\u0631\u064a\u062e\u064a",       # tarikhi (historical)
    ],
    "science": [
        "\u0639\u0644\u0645",           # ilm (science)
        "\u0639\u0644\u0648\u0645",         # ulum (sciences)
    ],
    "medicine": [
        "\u0637\u0628",             # tibb (medicine)
        "\u0637\u0628\u064a",           # tibbi (medical)
        "\u0635\u062d\u0629",           # sihha (health)
    ],
    "virology": [
        "\u0641\u064a\u0631\u0648\u0633",         # firus (virus)
        "\u0641\u064a\u0631\u0648\u0633\u0627\u062a",     # firusat (viruses)
        "\u0639\u0644\u0645 \u0627\u0644\u0641\u064a\u0631\u0648\u0633\u0627\u062a",   # ilm al-firusat (virology)
    ],
}


# ============================================================
# CHINESE TERMS
# ============================================================

CHINESE_ACADEMIC_TERMS: list[str] = [
    "\u7814\u7a76",     # yanjiu (research)
    "\u8bba\u6587",     # lunwen (thesis/paper)
    "\u5b66\u672f",     # xueshu (academic)
    "\u671f\u520a",     # qikan (journal)
    "\u62a5\u544a",     # baogao (report)
    "\u5206\u6790",     # fenxi (analysis)
]

CHINESE_TOPIC_TERMS: dict[str, list[str]] = {
    "archaeology": [
        "\u8003\u53e4\u5b66",   # kaogu xue (archaeology)
        "\u8003\u53e4",     # kaogu (archaeological)
        "\u53d1\u6398",     # fajue (excavation)
        "\u6587\u7269",     # wenwu (cultural relics)
        "\u9057\u5740",     # yizhi (site/ruins)
    ],
    "history": [
        "\u5386\u53f2",     # lishi (history)
        "\u53e4\u4ee3",     # gudai (ancient)
    ],
    "science": [
        "\u79d1\u5b66",     # kexue (science)
        "\u6280\u672f",     # jishu (technology)
    ],
    "medicine": [
        "\u533b\u5b66",     # yixue (medicine)
        "\u4e34\u5e8a",     # linchuang (clinical)
    ],
    "virology": [
        "\u75c5\u6bd2\u5b66",   # bingdu xue (virology)
        "\u75c5\u6bd2",     # bingdu (virus)
        "\u4f20\u67d3\u75c5",   # chuanranbing (infectious disease)
    ],
}


# ============================================================
# JAPANESE TERMS
# ============================================================

JAPANESE_ACADEMIC_TERMS: list[str] = [
    "\u7814\u7a76",     # kenkyu (research)
    "\u8ad6\u6587",     # ronbun (paper/thesis)
    "\u5b66\u8853",     # gakujutsu (academic)
    "\u8abf\u67fb",     # chosa (investigation)
    "\u5831\u544a",     # hokoku (report)
    "\u5206\u6790",     # bunseki (analysis)
]

JAPANESE_TOPIC_TERMS: dict[str, list[str]] = {
    "archaeology": [
        "\u8003\u53e4\u5b66",     # kokogaku (archaeology)
        "\u767a\u6398",       # hakkutsu (excavation)
        "\u907a\u8de1",       # iseki (ruins/site)
        "\u6587\u5316\u8ca1",     # bunkazai (cultural property)
    ],
    "history": [
        "\u6b74\u53f2",       # rekishi (history)
        "\u53e4\u4ee3",       # kodai (ancient)
    ],
    "science": [
        "\u79d1\u5b66",       # kagaku (science)
        "\u6280\u8853",       # gijutsu (technology)
    ],
    "medicine": [
        "\u533b\u5b66",       # igaku (medicine)
        "\u81e8\u5e8a",       # rinsho (clinical)
    ],
    "virology": [
        "\u30a6\u30a4\u30eb\u30b9\u5b66",   # uirusu-gaku (virology)
        "\u30a6\u30a4\u30eb\u30b9",     # uirusu (virus)
        "\u611f\u67d3\u75c7",     # kansensho (infectious disease)
    ],
}


# ============================================================
# KOREAN TERMS
# ============================================================

KOREAN_ACADEMIC_TERMS: list[str] = [
    "\uc5f0\uad6c",     # yeongu (research)
    "\ub17c\ubb38",     # nonmun (paper/thesis)
    "\ud559\uc220",     # haksul (academic)
    "\ubcf4\uace0\uc11c",   # bogoseo (report)
    "\ubd84\uc11d",     # bunseok (analysis)
    "\uc870\uc0ac",     # josa (investigation)
]

KOREAN_TOPIC_TERMS: dict[str, list[str]] = {
    "archaeology": [
        "\uace0\uace0\ud559",     # gogohak (archaeology)
        "\ubc1c\uad74",       # balgul (excavation)
        "\uc720\uc801",       # yujeok (ruins/site)
        "\ubb38\ud654\uc7ac",     # munhwajae (cultural property)
    ],
    "history": [
        "\uc5ed\uc0ac",       # yeoksa (history)
        "\uace0\ub300",       # godae (ancient)
    ],
    "science": [
        "\uacfc\ud559",       # gwahak (science)
        "\uae30\uc220",       # gisul (technology)
    ],
    "medicine": [
        "\uc758\ud559",       # uihak (medicine)
        "\uc784\uc0c1",       # imsang (clinical)
    ],
    "virology": [
        "\ubc14\uc774\ub7ec\uc2a4\ud559",   # baireoseu-hak (virology)
        "\ubc14\uc774\ub7ec\uc2a4",     # baireoseu (virus)
        "\uac10\uc5fc\ubcd1",     # gamyeombyeong (infectious disease)
    ],
}


# ============================================================
# LOCALIZATION FUNCTIONS
# ============================================================

def _find_discipline_key(discipline: str) -> str:
    """Map a discipline name to a topic term dictionary key."""
    discipline_lower = discipline.lower().strip()
    # Direct match
    for key in ("archaeology", "history", "science", "medicine", "virology"):
        if key in discipline_lower:
            return key
    # Default to science
    return "science"


def _generate_arabic_queries(topic: str, discipline: str) -> list[str]:
    """Generate Arabic queries with morphological expansion."""
    disc_key = _find_discipline_key(discipline)
    topic_terms = ARABIC_TOPIC_TERMS.get(disc_key, ARABIC_TOPIC_TERMS["science"])
    queries: list[str] = []

    # Combine academic terms with topic terms
    for academic in ARABIC_ACADEMIC_TERMS[:3]:  # top 3 academic terms
        for topic_term in topic_terms[:2]:       # top 2 topic terms
            queries.append(f"{academic} {topic_term} {topic}")

    # Add pure topic term queries
    for topic_term in topic_terms:
        queries.append(f"{topic_term} {topic}")

    return queries


def _generate_chinese_queries(topic: str, discipline: str) -> list[str]:
    """Generate Chinese queries with phrasal compounds."""
    disc_key = _find_discipline_key(discipline)
    topic_terms = CHINESE_TOPIC_TERMS.get(disc_key, CHINESE_TOPIC_TERMS["science"])
    queries: list[str] = []

    # Combine academic terms with topic terms (no spaces, Chinese style)
    for academic in CHINESE_ACADEMIC_TERMS[:3]:
        for topic_term in topic_terms[:2]:
            queries.append(f"{topic_term}{academic}")

    # Add topic + transliteration queries
    for topic_term in topic_terms:
        queries.append(f"{topic_term} {topic}")

    return queries


def _generate_japanese_queries(topic: str, discipline: str) -> list[str]:
    """Generate Japanese queries with kanji + katakana."""
    disc_key = _find_discipline_key(discipline)
    topic_terms = JAPANESE_TOPIC_TERMS.get(disc_key, JAPANESE_TOPIC_TERMS["science"])
    queries: list[str] = []

    # Combine academic terms with topic terms
    for academic in JAPANESE_ACADEMIC_TERMS[:3]:
        for topic_term in topic_terms[:2]:
            queries.append(f"{topic_term} {academic}")

    # Add topic term + English topic
    for topic_term in topic_terms:
        queries.append(f"{topic_term} {topic}")

    return queries


def _generate_korean_queries(topic: str, discipline: str) -> list[str]:
    """Generate Korean queries with hangul compounds."""
    disc_key = _find_discipline_key(discipline)
    topic_terms = KOREAN_TOPIC_TERMS.get(disc_key, KOREAN_TOPIC_TERMS["science"])
    queries: list[str] = []

    # Combine academic terms with topic terms
    for academic in KOREAN_ACADEMIC_TERMS[:3]:
        for topic_term in topic_terms[:2]:
            queries.append(f"{topic_term} {academic}")

    # Add topic term + English topic
    for topic_term in topic_terms:
        queries.append(f"{topic_term} {topic}")

    return queries


# Dispatcher
_GENERATORS: dict[str, object] = {
    "ar": _generate_arabic_queries,
    "zh": _generate_chinese_queries,
    "ja": _generate_japanese_queries,
    "ko": _generate_korean_queries,
}


def localize_query(
    topic: str, language: str, discipline: str
) -> list[str]:
    """Generate culturally-aware localized queries for a language.

    Args:
        topic: The research topic (in English).
        language: ISO 639-1 language code.
        discipline: The academic discipline.

    Returns:
        List of localized query strings. Empty list if language
        is not supported for localization.
    """
    generator = _GENERATORS.get(language)
    if generator is None:
        return []
    return generator(topic, discipline)


def localize_query_via_llm(
    topic: str,
    language: str,
    discipline: str,
    connector: BaseConnector,
) -> list[str]:
    """Generate localized queries using an LLM connector as fallback.

    Uses the connector's generate_localized_queries method for
    languages where static term lists may be insufficient.

    Args:
        topic: The research topic (in English).
        language: ISO 639-1 language code.
        discipline: The academic discipline.
        connector: A BaseConnector instance (MockConnector or ClaudeConnector).

    Returns:
        List of localized query strings from the LLM.
    """
    return connector.generate_localized_queries(topic, language, discipline)
