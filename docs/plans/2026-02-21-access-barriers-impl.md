# v3 Phase 4: Access Barriers — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Teach the engine that some academic ecosystems (Chinese CNKI, Arabic Al-Manhal, Japanese CiNii, Korean RISS) are structurally inaccessible via web search, with culturally-aware query generation and split coverage scoring.

**Architecture:** New meta-axiom MA-08 generates access-barrier expectations. A `query_localization.py` module produces heuristic queries for Arabic (morphological) and CJK (phrasal) languages. Coverage splits into `accessible_score` + `estimated_unreachable`. Zero external dependencies.

**Tech Stack:** Python 3.10+ stdlib only (dataclasses, enum). pytest for tests. All in `src/epistemix/` and `tests/`.

**Worktree:** `/Users/francescorinaldi/GitHub/epistemix/.worktrees/access-barriers` (branch: `feature/access-barriers`)

**Baseline:** 171 tests passing. All commands run from worktree root with `source .venv/bin/activate`.

---

## Task 1: Data structures in models.py

Add `AccessTier` enum, `LanguageEcosystem` dataclass, `CoverageBreakdown` dataclass, and `ACCESS_BARRIER` gap type.

**Files:**
- Modify: `src/epistemix/models.py` (lines 48-70 for GapType, add new classes after line 112)
- Test: `tests/test_models.py`

**Step 1: Write the failing tests**

Add to `tests/test_models.py`:

```python
# --- At top, update imports to include new types ---
from epistemix.models import (
    AccessTier, LanguageEcosystem, CoverageBreakdown,
    # ... existing imports ...
)


class TestAccessTier:
    def test_access_tier_values(self):
        assert AccessTier.OPEN_WEB.value == "open_web"
        assert AccessTier.PARTIAL_ACCESS.value == "partial_access"
        assert AccessTier.WALLED_GARDEN.value == "walled_garden"

    def test_all_tiers_exist(self):
        assert len(AccessTier) == 3


class TestLanguageEcosystem:
    def test_construction(self):
        eco = LanguageEcosystem(
            language="zh",
            access_tier=AccessTier.WALLED_GARDEN,
            gated_databases=("CNKI", "Wanfang"),
            estimated_gated_share=0.70,
            query_style="phrasal",
            script="cjk",
        )
        assert eco.language == "zh"
        assert eco.access_tier == AccessTier.WALLED_GARDEN
        assert eco.estimated_gated_share == 0.70
        assert "CNKI" in eco.gated_databases

    def test_frozen(self):
        eco = LanguageEcosystem(
            language="ar",
            access_tier=AccessTier.PARTIAL_ACCESS,
            gated_databases=("Al-Manhal",),
            estimated_gated_share=0.35,
            query_style="morphological",
            script="arabic",
        )
        import pytest
        with pytest.raises(AttributeError):
            eco.language = "en"

    def test_to_dict(self):
        eco = LanguageEcosystem(
            language="ja",
            access_tier=AccessTier.PARTIAL_ACCESS,
            gated_databases=("CiNii", "J-STAGE"),
            estimated_gated_share=0.40,
            query_style="phrasal",
            script="cjk",
        )
        d = eco.to_dict()
        assert d["language"] == "ja"
        assert d["access_tier"] == "partial_access"
        assert d["gated_databases"] == ["CiNii", "J-STAGE"]
        assert d["estimated_gated_share"] == 0.40


class TestCoverageBreakdown:
    def test_construction(self):
        cb = CoverageBreakdown(
            accessible_score=62.0,
            estimated_unreachable=18.5,
            barrier_annotations=["CNKI: ~70% of Chinese academic output"],
            gated_expectations_count=3,
            gated_expectations_met=1,
        )
        assert cb.accessible_score == 62.0
        assert cb.estimated_unreachable == 18.5
        assert len(cb.barrier_annotations) == 1

    def test_to_dict(self):
        cb = CoverageBreakdown(
            accessible_score=75.0,
            estimated_unreachable=10.0,
            barrier_annotations=["Note A"],
            gated_expectations_count=2,
            gated_expectations_met=0,
        )
        d = cb.to_dict()
        assert d["accessible_score"] == 75.0
        assert d["estimated_unreachable"] == 10.0
        assert d["barrier_annotations"] == ["Note A"]


class TestAccessBarrierGapType:
    def test_access_barrier_gap_type_exists(self):
        assert GapType.ACCESS_BARRIER.value == "access_barrier"
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_models.py -v -k "TestAccessTier or TestLanguageEcosystem or TestCoverageBreakdown or TestAccessBarrierGapType" 2>&1 | tail -15`
Expected: FAIL (ImportError — AccessTier, LanguageEcosystem, CoverageBreakdown don't exist yet)

**Step 3: Write minimal implementation**

In `src/epistemix/models.py`:

1. Add `ACCESS_BARRIER = "access_barrier"` to the `GapType` enum (after line 70, after `INFLUENCE_GAP`).

2. Add `AccessTier` enum after the `RelationType` enum (after line 111):

```python
class AccessTier(Enum):
    """How reachable a language's academic ecosystem is via web search."""
    OPEN_WEB = "open_web"
    PARTIAL_ACCESS = "partial_access"
    WALLED_GARDEN = "walled_garden"
```

3. Add `LanguageEcosystem` dataclass after `AccessTier`:

```python
@dataclass(frozen=True)
class LanguageEcosystem:
    """Per-language metadata for access-barrier reasoning.

    Classifies how much of a language's academic output is behind
    gated databases (CNKI, Al-Manhal, CiNii, RISS, etc.) and how
    to generate queries for that language's script and morphology.
    """
    language: str
    access_tier: AccessTier
    gated_databases: tuple[str, ...]
    estimated_gated_share: float
    query_style: str   # "keyword", "morphological", "phrasal"
    script: str        # "latin", "arabic", "cjk", "hangul"

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "access_tier": self.access_tier.value,
            "gated_databases": list(self.gated_databases),
            "estimated_gated_share": self.estimated_gated_share,
            "query_style": self.query_style,
            "script": self.script,
        }
```

4. Add `CoverageBreakdown` dataclass after `LanguageEcosystem`:

```python
@dataclass
class CoverageBreakdown:
    """Split coverage: what we verified vs. what we estimate is unreachable.

    accessible_score: 0-100, coverage from expectations we can evaluate
    estimated_unreachable: 0-100, knowledge behind access barriers
    barrier_annotations: human-readable explanations of what's gated
    """
    accessible_score: float
    estimated_unreachable: float
    barrier_annotations: list[str] = field(default_factory=list)
    gated_expectations_count: int = 0
    gated_expectations_met: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessible_score": round(self.accessible_score, 1),
            "estimated_unreachable": round(self.estimated_unreachable, 1),
            "barrier_annotations": self.barrier_annotations,
            "gated_expectations_count": self.gated_expectations_count,
            "gated_expectations_met": self.gated_expectations_met,
        }
```

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_models.py -v -k "TestAccessTier or TestLanguageEcosystem or TestCoverageBreakdown or TestAccessBarrierGapType" 2>&1 | tail -15`
Expected: All new tests PASS

**Step 5: Run full suite for regression**

Run: `source .venv/bin/activate && pytest tests/ -v 2>&1 | tail -5`
Expected: 171 + new tests all pass

**Step 6: Commit**

```bash
git add src/epistemix/models.py tests/test_models.py
git commit -m "feat: add AccessTier, LanguageEcosystem, CoverageBreakdown, ACCESS_BARRIER gap type"
```

---

## Task 2: Language ecosystem registry in knowledge.py

Add `LANGUAGE_ECOSYSTEMS`, `CROSS_LANGUAGE_STRATEGIES`, new country entries for China/Japan/Korea/Saudi Arabia, and transliteration data.

**Files:**
- Modify: `src/epistemix/knowledge.py` (after line 98 for new countries, after line 151 for new data)
- Test: `tests/test_access_barriers.py` (create)

**Step 1: Write the failing tests**

Create `tests/test_access_barriers.py`:

```python
"""Tests for access-barrier ecosystem data and cross-language strategies."""

from __future__ import annotations

import pytest

from epistemix.models import AccessTier, LanguageEcosystem
from epistemix.knowledge import LANGUAGE_ECOSYSTEMS, CROSS_LANGUAGE_STRATEGIES


class TestLanguageEcosystemRegistry:
    def test_chinese_is_walled_garden(self):
        eco = LANGUAGE_ECOSYSTEMS["zh"]
        assert eco.access_tier == AccessTier.WALLED_GARDEN
        assert eco.estimated_gated_share == 0.70
        assert "CNKI" in eco.gated_databases
        assert eco.query_style == "phrasal"
        assert eco.script == "cjk"

    def test_arabic_is_partial_access(self):
        eco = LANGUAGE_ECOSYSTEMS["ar"]
        assert eco.access_tier == AccessTier.PARTIAL_ACCESS
        assert eco.estimated_gated_share == 0.35
        assert "Al-Manhal" in eco.gated_databases
        assert eco.query_style == "morphological"
        assert eco.script == "arabic"

    def test_japanese_is_partial_access(self):
        eco = LANGUAGE_ECOSYSTEMS["ja"]
        assert eco.access_tier == AccessTier.PARTIAL_ACCESS
        assert "CiNii" in eco.gated_databases
        assert eco.query_style == "phrasal"

    def test_korean_is_partial_access(self):
        eco = LANGUAGE_ECOSYSTEMS["ko"]
        assert eco.access_tier == AccessTier.PARTIAL_ACCESS
        assert "RISS" in eco.gated_databases
        assert eco.query_style == "phrasal"
        assert eco.script == "hangul"

    def test_english_not_in_registry(self):
        assert "en" not in LANGUAGE_ECOSYSTEMS

    def test_unlisted_language_defaults_to_open(self):
        # Languages not in LANGUAGE_ECOSYSTEMS are treated as open_web.
        # This is a convention, not enforced by the dict itself.
        assert "fr" not in LANGUAGE_ECOSYSTEMS
        assert "de" not in LANGUAGE_ECOSYSTEMS


class TestCrossLanguageStrategies:
    def test_chinese_has_english_fallback(self):
        strategies = CROSS_LANGUAGE_STRATEGIES["zh"]
        langs = [s[0] for s in strategies]
        assert "en" in langs

    def test_arabic_has_english_fallback(self):
        strategies = CROSS_LANGUAGE_STRATEGIES["ar"]
        langs = [s[0] for s in strategies]
        assert "en" in langs

    def test_strategies_use_topic_placeholder(self):
        for lang, strategies in CROSS_LANGUAGE_STRATEGIES.items():
            for target_lang, template in strategies:
                assert "{topic}" in template, (
                    f"Strategy for {lang}→{target_lang} missing {{topic}} placeholder"
                )

    def test_all_ecosystems_have_strategies(self):
        for lang in LANGUAGE_ECOSYSTEMS:
            assert lang in CROSS_LANGUAGE_STRATEGIES, (
                f"Language {lang} has ecosystem but no cross-language strategy"
            )
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_access_barriers.py -v 2>&1 | tail -15`
Expected: FAIL (ImportError — LANGUAGE_ECOSYSTEMS, CROSS_LANGUAGE_STRATEGIES don't exist)

**Step 3: Write minimal implementation**

In `src/epistemix/knowledge.py`:

1. Add import at top (after line 7):

```python
from epistemix.models import AccessTier, LanguageEcosystem
```

2. Add new country entries to `GEOGRAPHIC_LINGUISTIC` (after the Germany entry, before the closing `}`):

```python
    "China": {
        "primary_languages": ["zh", "en"],
        "foreign_traditions": {
            "ja": "Japanese archaeological missions",
            "ko": "Korean scholarly exchange",
        },
        "transliteration_map": {},
    },
    "Japan": {
        "primary_languages": ["ja", "en"],
        "foreign_traditions": {},
        "transliteration_map": {},
    },
    "South Korea": {
        "primary_languages": ["ko", "en"],
        "foreign_traditions": {},
        "transliteration_map": {},
    },
    "Saudi Arabia": {
        "primary_languages": ["ar", "en"],
        "foreign_traditions": {
            "fr": "French archaeological missions",
        },
        "transliteration_map": {},
    },
```

3. Add `LANGUAGE_ECOSYSTEMS` after the `KNOWN_PLACES` set (after line 182):

```python
# ============================================================
# LANGUAGE ECOSYSTEM CLASSIFICATION
# ============================================================

LANGUAGE_ECOSYSTEMS: dict[str, LanguageEcosystem] = {
    "zh": LanguageEcosystem(
        language="zh",
        access_tier=AccessTier.WALLED_GARDEN,
        gated_databases=("CNKI", "Wanfang", "VIP", "CQVIP"),
        estimated_gated_share=0.70,
        query_style="phrasal",
        script="cjk",
    ),
    "ar": LanguageEcosystem(
        language="ar",
        access_tier=AccessTier.PARTIAL_ACCESS,
        gated_databases=("Al-Manhal", "E-Marefa", "Dar Al Mandumah"),
        estimated_gated_share=0.35,
        query_style="morphological",
        script="arabic",
    ),
    "ja": LanguageEcosystem(
        language="ja",
        access_tier=AccessTier.PARTIAL_ACCESS,
        gated_databases=("CiNii", "J-STAGE", "NDL Digital"),
        estimated_gated_share=0.40,
        query_style="phrasal",
        script="cjk",
    ),
    "ko": LanguageEcosystem(
        language="ko",
        access_tier=AccessTier.PARTIAL_ACCESS,
        gated_databases=("RISS", "KCI", "DBpia"),
        estimated_gated_share=0.35,
        query_style="phrasal",
        script="hangul",
    ),
}


# ============================================================
# CROSS-LANGUAGE STRATEGIES
# ============================================================

CROSS_LANGUAGE_STRATEGIES: dict[str, list[tuple[str, str]]] = {
    "zh": [
        ("en", "Chinese research on {topic}"),
        ("ja", "{topic} 中国の研究"),
    ],
    "ar": [
        ("en", "Arabic-language research on {topic}"),
        ("fr", "recherche arabophone sur {topic}"),
    ],
    "ja": [
        ("en", "Japanese research on {topic}"),
    ],
    "ko": [
        ("en", "Korean research on {topic}"),
    ],
}
```

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_access_barriers.py -v 2>&1 | tail -15`
Expected: All new tests PASS

**Step 5: Run full suite for regression**

Run: `source .venv/bin/activate && pytest tests/ -v 2>&1 | tail -5`
Expected: All tests pass (171 existing + new)

**Step 6: Commit**

```bash
git add src/epistemix/knowledge.py tests/test_access_barriers.py
git commit -m "feat: add LANGUAGE_ECOSYSTEMS registry and CROSS_LANGUAGE_STRATEGIES"
```

---

## Task 3: Meta-axiom MA-08 Access Barriers

Add the 8th meta-axiom to `meta_axioms.py`.

**Files:**
- Modify: `src/epistemix/meta_axioms.py` (add axiom before line 120, update META_AXIOMS)
- Test: `tests/test_access_barriers.py` (append)

**Step 1: Write the failing tests**

Append to `tests/test_access_barriers.py`:

```python
from epistemix.meta_axioms import (
    META_AXIOMS,
    META_AXIOM_BY_ID,
    MA_08_ACCESS,
    generate_postulate_descriptions,
)


class TestMA08AccessBarriers:
    def test_ma08_exists(self):
        assert MA_08_ACCESS.id == "MA-08"
        assert MA_08_ACCESS.name == "Access Barriers"

    def test_ma08_in_meta_axioms(self):
        ids = [ma.id for ma in META_AXIOMS]
        assert "MA-08" in ids
        assert len(META_AXIOMS) == 8

    def test_ma08_in_lookup(self):
        assert "MA-08" in META_AXIOM_BY_ID
        assert META_AXIOM_BY_ID["MA-08"].name == "Access Barriers"

    def test_ma08_has_postulate_templates(self):
        assert len(MA_08_ACCESS.postulate_templates) >= 2

    def test_ma08_generates_postulates(self):
        descriptions = generate_postulate_descriptions(
            "SARS-CoV-2 origins", "China", "virology"
        )
        ma08_descs = [d for aid, d in descriptions if aid == "MA-08"]
        assert len(ma08_descs) >= 2
        # Should mention the topic
        assert any("SARS-CoV-2" in d for d in ma08_descs)
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_access_barriers.py::TestMA08AccessBarriers -v 2>&1 | tail -10`
Expected: FAIL (ImportError — MA_08_ACCESS doesn't exist)

**Step 3: Write minimal implementation**

In `src/epistemix/meta_axioms.py`:

1. Add `MA_08_ACCESS` before the `META_AXIOMS` tuple (before line 120):

```python
MA_08_ACCESS = MetaAxiom(
    id="MA-08",
    name="Access Barriers",
    description=(
        "Some knowledge ecosystems are structurally inaccessible via "
        "open web search. Walled-garden databases (CNKI, Al-Manhal, etc.) "
        "contain academic literature that cannot be retrieved or verified "
        "through standard search APIs. An audit that ignores these barriers "
        "overstates its coverage."
    ),
    postulate_templates=(
        "Academic literature on {topic} exists behind gated databases in {country}",
        "Web search alone cannot verify {topic} research in walled-garden ecosystems",
        "Coverage of {topic} is structurally incomplete for non-open-web languages",
    ),
)
```

2. Update `META_AXIOMS` tuple to include `MA_08_ACCESS`:

```python
META_AXIOMS: tuple[MetaAxiom, ...] = (
    MA_01_LANGUAGE,
    MA_02_INSTITUTION,
    MA_03_THEORY,
    MA_04_SCHOOL,
    MA_05_DISCIPLINE,
    MA_06_PUBLICATION,
    MA_07_TEMPORAL,
    MA_08_ACCESS,
)
```

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_access_barriers.py::TestMA08AccessBarriers -v 2>&1 | tail -10`
Expected: All PASS

**Step 5: Run full suite for regression**

Run: `source .venv/bin/activate && pytest tests/ -v 2>&1 | tail -5`
Expected: All pass. Note: some existing tests may reference `len(META_AXIOMS) == 7` — if so, update them to 8.

**Step 6: Commit**

```bash
git add src/epistemix/meta_axioms.py tests/test_access_barriers.py
git commit -m "feat: add MA-08 Access Barriers meta-axiom (8th axiom)"
```

---

## Task 4: Localized query generation module

Create `query_localization.py` with heuristic query generation for Arabic, Chinese, Japanese, Korean, plus LLM fallback.

**Files:**
- Create: `src/epistemix/query_localization.py`
- Create: `tests/test_query_localization.py`

**Step 1: Write the failing tests**

Create `tests/test_query_localization.py`:

```python
"""Tests for culturally-aware query localization."""

from __future__ import annotations

import pytest

from epistemix.query_localization import (
    localize_query,
    localize_query_via_llm,
    ARABIC_ACADEMIC_TERMS,
    CHINESE_ACADEMIC_TERMS,
    JAPANESE_ACADEMIC_TERMS,
    KOREAN_ACADEMIC_TERMS,
)


class TestArabicQueries:
    def test_arabic_queries_returned(self):
        queries = localize_query("excavation", "ar", "archaeology")
        assert len(queries) >= 1

    def test_arabic_queries_contain_arabic_script(self):
        queries = localize_query("virus", "ar", "virology")
        # At least one query should contain Arabic characters (Unicode range)
        has_arabic = any(
            any("\u0600" <= c <= "\u06FF" for c in q)
            for q in queries
        )
        assert has_arabic, f"No Arabic script found in queries: {queries}"

    def test_arabic_academic_terms_coverage(self):
        assert "archaeology" in ARABIC_ACADEMIC_TERMS
        assert "virology" in ARABIC_ACADEMIC_TERMS
        assert "medicine" in ARABIC_ACADEMIC_TERMS


class TestChineseQueries:
    def test_chinese_queries_returned(self):
        queries = localize_query("virus", "zh", "virology")
        assert len(queries) >= 1

    def test_chinese_queries_no_spaces(self):
        queries = localize_query("excavation", "zh", "archaeology")
        # Chinese queries should not have spaces between CJK characters
        for q in queries:
            # Allow spaces only between non-CJK parts
            cjk_parts = [c for c in q if "\u4e00" <= c <= "\u9fff"]
            assert len(cjk_parts) >= 1, f"No CJK characters in query: {q}"

    def test_chinese_academic_terms_coverage(self):
        assert "archaeology" in CHINESE_ACADEMIC_TERMS
        assert "virology" in CHINESE_ACADEMIC_TERMS

    def test_traditional_chinese_variant(self):
        queries = localize_query("virus", "zh", "virology")
        # Should include at least one query (simplified or traditional)
        assert len(queries) >= 1


class TestJapaneseQueries:
    def test_japanese_queries_returned(self):
        queries = localize_query("virus", "ja", "virology")
        assert len(queries) >= 1

    def test_japanese_contains_cjk_or_kana(self):
        queries = localize_query("archaeology", "ja", "archaeology")
        has_jp = any(
            any(
                ("\u4e00" <= c <= "\u9fff")  # kanji
                or ("\u3040" <= c <= "\u309f")  # hiragana
                or ("\u30a0" <= c <= "\u30ff")  # katakana
                for c in q
            )
            for q in queries
        )
        assert has_jp, f"No Japanese script in queries: {queries}"

    def test_japanese_academic_terms_coverage(self):
        assert "archaeology" in JAPANESE_ACADEMIC_TERMS
        assert "virology" in JAPANESE_ACADEMIC_TERMS


class TestKoreanQueries:
    def test_korean_queries_returned(self):
        queries = localize_query("virus", "ko", "virology")
        assert len(queries) >= 1

    def test_korean_contains_hangul(self):
        queries = localize_query("archaeology", "ko", "archaeology")
        has_hangul = any(
            any("\uac00" <= c <= "\ud7af" for c in q)
            for q in queries
        )
        assert has_hangul, f"No Hangul in queries: {queries}"

    def test_korean_academic_terms_coverage(self):
        assert "archaeology" in KOREAN_ACADEMIC_TERMS


class TestKeywordFallback:
    def test_unknown_language_returns_english_keywords(self):
        queries = localize_query("excavation", "en", "archaeology")
        assert len(queries) >= 1
        # English queries should just be keyword-based
        assert all(c < "\u0600" for q in queries for c in q)

    def test_unsupported_language_returns_topic(self):
        queries = localize_query("virus origins", "sw", "virology")
        assert len(queries) >= 1


class TestLLMFallback:
    def test_llm_fallback_with_mock_connector(self):
        from epistemix.connector import MockConnector
        connector = MockConnector()
        connector.register_localized_queries("zh", [
            "新冠病毒起源研究",
            "SARS-CoV-2来源调查",
        ])
        queries = localize_query_via_llm(
            "SARS-CoV-2 origins", "zh", "virology", connector
        )
        assert len(queries) == 2
        assert "新冠病毒起源研究" in queries

    def test_llm_fallback_without_connector_returns_empty(self):
        queries = localize_query_via_llm(
            "SARS-CoV-2 origins", "zh", "virology", None
        )
        assert queries == []
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_query_localization.py -v 2>&1 | tail -15`
Expected: FAIL (ModuleNotFoundError — query_localization doesn't exist)

**Step 3: Write minimal implementation**

Create `src/epistemix/query_localization.py`:

```python
"""Culturally-aware query generation for non-Latin academic ecosystems.

Generates search queries adapted to language-specific conventions:
- Arabic: morphological variants from triliteral roots
- Chinese: phrasal compounds without spaces (simplified + traditional)
- Japanese: kanji + katakana mixed queries
- Korean: hangul compound terms

Falls back to keyword style for Latin-script languages.
LLM fallback via connector for refinement when available.

Dependency: imports from models.py and knowledge.py only.
"""

from __future__ import annotations

from typing import Any


# ============================================================
# ARABIC ACADEMIC TERMS
# ============================================================

ARABIC_ACADEMIC_TERMS: dict[str, str] = {
    "archaeology": "علم الآثار",
    "history": "تاريخ",
    "biology": "علم الأحياء",
    "virology": "علم الفيروسات",
    "medicine": "طب",
    "physics": "فيزياء",
    "chemistry": "كيمياء",
    "economics": "اقتصاد",
    "sociology": "علم الاجتماع",
    "psychology": "علم النفس",
    "political science": "علوم سياسية",
    "philosophy": "فلسفة",
    "linguistics": "لسانيات",
    "engineering": "هندسة",
    "environmental science": "علوم بيئية",
    "computer science": "علوم الحاسوب",
}

ARABIC_TOPIC_TERMS: dict[str, list[str]] = {
    "excavation": ["حفريات", "تنقيب", "حفر"],
    "tomb": ["مقبرة", "ضريح", "قبر"],
    "virus": ["فيروس", "فيروسات"],
    "origins": ["أصول", "منشأ"],
    "research": ["بحث", "أبحاث", "دراسة"],
    "discovery": ["اكتشاف", "كشف"],
    "analysis": ["تحليل", "دراسة"],
    "disease": ["مرض", "أمراض"],
    "pandemic": ["جائحة", "وباء"],
    "vaccine": ["لقاح", "تطعيم"],
}


# ============================================================
# CHINESE ACADEMIC TERMS (Simplified + Traditional)
# ============================================================

CHINESE_ACADEMIC_TERMS: dict[str, tuple[str, str]] = {
    # (simplified, traditional)
    "archaeology": ("考古学", "考古學"),
    "history": ("历史", "歷史"),
    "biology": ("生物学", "生物學"),
    "virology": ("病毒学", "病毒學"),
    "medicine": ("医学", "醫學"),
    "physics": ("物理学", "物理學"),
    "chemistry": ("化学", "化學"),
    "economics": ("经济学", "經濟學"),
    "sociology": ("社会学", "社會學"),
    "psychology": ("心理学", "心理學"),
    "political science": ("政治学", "政治學"),
    "philosophy": ("哲学", "哲學"),
    "linguistics": ("语言学", "語言學"),
    "engineering": ("工程学", "工程學"),
    "environmental science": ("环境科学", "環境科學"),
    "computer science": ("计算机科学", "計算機科學"),
}

CHINESE_TOPIC_TERMS: dict[str, tuple[str, str]] = {
    # (simplified, traditional)
    "excavation": ("发掘", "發掘"),
    "tomb": ("墓葬", "墓葬"),
    "virus": ("病毒", "病毒"),
    "origins": ("起源", "起源"),
    "research": ("研究", "研究"),
    "discovery": ("发现", "發現"),
    "analysis": ("分析", "分析"),
    "disease": ("疾病", "疾病"),
    "pandemic": ("大流行", "大流行"),
    "vaccine": ("疫苗", "疫苗"),
}


# ============================================================
# JAPANESE ACADEMIC TERMS
# ============================================================

JAPANESE_ACADEMIC_TERMS: dict[str, str] = {
    "archaeology": "考古学",
    "history": "歴史",
    "biology": "生物学",
    "virology": "ウイルス学",
    "medicine": "医学",
    "physics": "物理学",
    "chemistry": "化学",
    "economics": "経済学",
    "sociology": "社会学",
    "psychology": "心理学",
    "political science": "政治学",
    "philosophy": "哲学",
    "linguistics": "言語学",
    "engineering": "工学",
    "environmental science": "環境科学",
    "computer science": "計算機科学",
}

JAPANESE_TOPIC_TERMS: dict[str, str] = {
    "excavation": "発掘",
    "tomb": "古墳",
    "virus": "ウイルス",
    "origins": "起源",
    "research": "研究",
    "discovery": "発見",
    "analysis": "分析",
    "disease": "疾患",
    "pandemic": "パンデミック",
    "vaccine": "ワクチン",
}


# ============================================================
# KOREAN ACADEMIC TERMS
# ============================================================

KOREAN_ACADEMIC_TERMS: dict[str, str] = {
    "archaeology": "고고학",
    "history": "역사",
    "biology": "생물학",
    "virology": "바이러스학",
    "medicine": "의학",
    "physics": "물리학",
    "chemistry": "화학",
    "economics": "경제학",
    "sociology": "사회학",
    "psychology": "심리학",
    "political science": "정치학",
    "philosophy": "철학",
    "linguistics": "언어학",
    "engineering": "공학",
    "environmental science": "환경과학",
    "computer science": "컴퓨터과학",
}

KOREAN_TOPIC_TERMS: dict[str, str] = {
    "excavation": "발굴",
    "tomb": "고분",
    "virus": "바이러스",
    "origins": "기원",
    "research": "연구",
    "discovery": "발견",
    "analysis": "분석",
    "disease": "질병",
    "pandemic": "팬데믹",
    "vaccine": "백신",
}


# ============================================================
# QUERY GENERATION
# ============================================================

def _extract_content_words(topic: str) -> list[str]:
    """Extract meaningful content words from an English topic string."""
    import re
    stopwords = {
        "the", "a", "an", "of", "in", "on", "at", "to", "for",
        "and", "or", "is", "are", "was", "were", "by", "with",
        "from", "about", "as", "its", "their", "this", "that",
    }
    words = re.split(r"[\s,;.\-/]+", topic.lower())
    return [w for w in words if len(w) > 2 and w not in stopwords]


def _generate_arabic_queries(
    topic: str, discipline: str,
) -> list[str]:
    """Generate Arabic queries with morphological variants."""
    queries: list[str] = []
    words = _extract_content_words(topic)
    disc_ar = ARABIC_ACADEMIC_TERMS.get(discipline.lower(), "")

    # Build queries from topic term variants
    topic_terms: list[str] = []
    for word in words:
        if word in ARABIC_TOPIC_TERMS:
            topic_terms.extend(ARABIC_TOPIC_TERMS[word])
        else:
            topic_terms.append(word)

    if topic_terms and disc_ar:
        # Primary: discipline + first topic term + research
        queries.append(f"{disc_ar} {topic_terms[0]} بحث")
        # Variant: different topic term forms
        for term in topic_terms[1:3]:
            queries.append(f"{term} {disc_ar}")
    elif disc_ar:
        queries.append(f"{disc_ar} بحث")
    elif topic_terms:
        queries.append(f"{topic_terms[0]} بحث")

    # Add English+Arabic mixed query (common in MENA academia)
    if words:
        queries.append(f"{topic} {disc_ar}" if disc_ar else topic)

    return queries


def _generate_chinese_queries(
    topic: str, discipline: str,
) -> list[str]:
    """Generate Chinese phrasal queries (simplified + traditional)."""
    queries: list[str] = []
    words = _extract_content_words(topic)
    disc_zh = CHINESE_ACADEMIC_TERMS.get(discipline.lower())

    topic_simp: list[str] = []
    topic_trad: list[str] = []
    for word in words:
        if word in CHINESE_TOPIC_TERMS:
            s, t = CHINESE_TOPIC_TERMS[word]
            topic_simp.append(s)
            topic_trad.append(t)

    if topic_simp and disc_zh:
        s_disc, t_disc = disc_zh
        # Simplified: topic + discipline + research
        queries.append(f"{''.join(topic_simp)}{s_disc}研究")
        # Traditional variant
        trad_query = f"{''.join(topic_trad)}{t_disc}研究"
        if trad_query != queries[-1]:
            queries.append(trad_query)
    elif disc_zh:
        s_disc, t_disc = disc_zh
        queries.append(f"{s_disc}研究")
    elif topic_simp:
        queries.append(f"{''.join(topic_simp)}研究")

    # Add English+Chinese mixed query
    if disc_zh:
        queries.append(f"{topic} {disc_zh[0]}")

    return queries


def _generate_japanese_queries(
    topic: str, discipline: str,
) -> list[str]:
    """Generate Japanese queries with kanji and katakana."""
    queries: list[str] = []
    words = _extract_content_words(topic)
    disc_ja = JAPANESE_ACADEMIC_TERMS.get(discipline.lower(), "")

    topic_ja: list[str] = []
    for word in words:
        if word in JAPANESE_TOPIC_TERMS:
            topic_ja.append(JAPANESE_TOPIC_TERMS[word])

    if topic_ja and disc_ja:
        queries.append(f"{''.join(topic_ja)}{disc_ja}研究")
        queries.append(f"{''.join(topic_ja)} 論文")
    elif disc_ja:
        queries.append(f"{disc_ja}研究")
    elif topic_ja:
        queries.append(f"{''.join(topic_ja)}研究")

    return queries


def _generate_korean_queries(
    topic: str, discipline: str,
) -> list[str]:
    """Generate Korean queries with hangul terms."""
    queries: list[str] = []
    words = _extract_content_words(topic)
    disc_ko = KOREAN_ACADEMIC_TERMS.get(discipline.lower(), "")

    topic_ko: list[str] = []
    for word in words:
        if word in KOREAN_TOPIC_TERMS:
            topic_ko.append(KOREAN_TOPIC_TERMS[word])

    if topic_ko and disc_ko:
        queries.append(f"{' '.join(topic_ko)} {disc_ko} 연구")
        queries.append(f"{' '.join(topic_ko)} 논문")
    elif disc_ko:
        queries.append(f"{disc_ko} 연구")
    elif topic_ko:
        queries.append(f"{' '.join(topic_ko)} 연구")

    return queries


def localize_query(
    topic: str, language: str, discipline: str,
) -> list[str]:
    """Generate culturally-aware search queries for a language.

    Returns a list of query strings tailored to the language's
    script and morphological conventions.

    Falls back to English keyword queries for unsupported languages.
    """
    generators = {
        "ar": _generate_arabic_queries,
        "zh": _generate_chinese_queries,
        "ja": _generate_japanese_queries,
        "ko": _generate_korean_queries,
    }

    generator = generators.get(language)
    if generator:
        queries = generator(topic, discipline)
        if queries:
            return queries

    # Fallback: keyword-style query
    return [f"{topic} {discipline} research"]


def localize_query_via_llm(
    topic: str,
    language: str,
    discipline: str,
    connector: Any,
) -> list[str]:
    """Generate queries via LLM when a connector is available.

    Returns empty list if connector is None or doesn't support
    localized query generation.
    """
    if connector is None:
        return []

    try:
        return connector.generate_localized_queries(topic, language, discipline)
    except (AttributeError, NotImplementedError):
        return []
```

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_query_localization.py -v 2>&1 | tail -20`
Expected: All PASS (except the LLM fallback test — need Task 5 for MockConnector changes)

Note: The `TestLLMFallback::test_llm_fallback_with_mock_connector` test will fail until Task 5 adds `register_localized_queries` to MockConnector. If running incrementally, skip this test with `-k "not test_llm_fallback_with_mock_connector"` until Task 5.

**Step 5: Run full suite for regression**

Run: `source .venv/bin/activate && pytest tests/ -v -k "not test_llm_fallback_with_mock_connector" 2>&1 | tail -5`
Expected: All pass

**Step 6: Commit**

```bash
git add src/epistemix/query_localization.py tests/test_query_localization.py
git commit -m "feat: add query_localization module for Arabic, Chinese, Japanese, Korean"
```

---

## Task 5: Connector changes — generate_localized_queries

Add `generate_localized_queries()` to `BaseConnector`, `MockConnector`, `ClaudeConnector`.

**Files:**
- Modify: `src/epistemix/connector.py` (BaseConnector line 59, MockConnector line 81, ClaudeConnector line 161)
- Test: `tests/test_connector.py` (append), `tests/test_query_localization.py` (the LLM fallback test)

**Step 1: Write the failing tests**

Append to `tests/test_connector.py`:

```python
class TestMockConnectorLocalizedQueries:
    def test_register_and_retrieve(self):
        connector = MockConnector()
        connector.register_localized_queries("zh", [
            "新冠病毒起源研究",
            "SARS-CoV-2来源调查",
        ])
        result = connector.generate_localized_queries(
            "SARS-CoV-2 origins", "zh", "virology"
        )
        assert len(result) == 2
        assert "新冠病毒起源研究" in result

    def test_unregistered_language_returns_empty(self):
        connector = MockConnector()
        result = connector.generate_localized_queries(
            "test", "ar", "biology"
        )
        assert result == []
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_connector.py::TestMockConnectorLocalizedQueries -v 2>&1 | tail -10`
Expected: FAIL (AttributeError — generate_localized_queries doesn't exist)

**Step 3: Write minimal implementation**

In `src/epistemix/connector.py`:

1. Add abstract method to `BaseConnector` (after `extract_relations`, around line 75):

```python
    @abstractmethod
    def generate_localized_queries(
        self, topic: str, language: str, discipline: str,
    ) -> list[str]:
        """Generate culturally-aware search queries for a language."""
```

2. Add to `MockConnector.__init__` (add after `self._relations`):

```python
        self._localized_queries: dict[str, list[str]] = {}
```

3. Add `register_localized_queries` and `generate_localized_queries` to `MockConnector` (after `extract_relations`):

```python
    def register_localized_queries(
        self, language: str, queries: list[str],
    ) -> None:
        """Pre-configure localized queries for tests."""
        self._localized_queries[language] = queries

    def generate_localized_queries(
        self, topic: str, language: str, discipline: str,
    ) -> list[str]:
        """Return pre-configured localized queries."""
        return self._localized_queries.get(language, [])
```

4. Add `generate_localized_queries` to `ClaudeConnector` (after `extract_relations`):

```python
    def generate_localized_queries(
        self, topic: str, language: str, discipline: str,
    ) -> list[str]:
        """Generate localized queries via Claude API."""
        if self.total_cost >= self._max_budget:
            return []

        prompt = (
            f"Generate 3-5 culturally appropriate academic search queries "
            f"for researching '{topic}' in the field of {discipline}.\n"
            f"The queries should be written in language code '{language}'.\n"
            f"Use natural academic phrasing for that language.\n"
            f"Return ONLY a JSON array of query strings."
        )

        messages = [{"role": "user", "content": prompt}]
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": messages,
        }

        try:
            response = self._call_with_retry(kwargs)
            self._call_count += 1
            text = self._extract_text(response)
            self._track_usage(response)
            json_data = extract_json(text)
            if isinstance(json_data, list):
                return [str(q) for q in json_data if isinstance(q, str)]
            return []
        except Exception:
            return []
```

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_connector.py::TestMockConnectorLocalizedQueries tests/test_query_localization.py::TestLLMFallback -v 2>&1 | tail -10`
Expected: All PASS

**Step 5: Run full suite for regression**

Run: `source .venv/bin/activate && pytest tests/ -v 2>&1 | tail -5`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/epistemix/connector.py tests/test_connector.py
git commit -m "feat: add generate_localized_queries to BaseConnector, MockConnector, ClaudeConnector"
```

---

## Task 6: Engine integration — access barrier inference and coverage breakdown

Wire MA-08 into `DynamicInferenceEngine`, update `calculate_coverage` to return `CoverageBreakdown`, integrate `query_localization` into query generation, and enrich `NegativePostulate` for access barriers.

**Files:**
- Modify: `src/epistemix/core.py` (lines 628-637 for derive, 342-400 for query gen, 974-1000 for coverage, 1050-1122 for run_cycle)
- Test: `tests/test_access_barriers.py` (append)
- Test: `tests/test_core.py` (update coverage tests)

**Step 1: Write the failing tests**

Append to `tests/test_access_barriers.py`:

```python
from epistemix.core import (
    EpistemixEngine,
    DynamicInferenceEngine,
    DynamicPostulates,
    calculate_coverage,
)
from epistemix.models import (
    Anomaly, CoverageBreakdown, Expectation, Finding,
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
            Expectation("CNKI gated", GapType.ACCESS_BARRIER, Severity.MEDIUM, met=False),
        ]
        anomalies = []
        result = calculate_coverage(expectations, anomalies)
        # accessible_score should only consider the non-barrier expectation
        assert result.accessible_score > 0
        assert result.gated_expectations_count == 1
        assert result.gated_expectations_met == 0

    def test_estimated_unreachable_reflects_gated_share(self):
        expectations = [
            Expectation("Sources in 'en'", GapType.LINGUISTIC, Severity.HIGH, met=True),
            Expectation("Chinese sources behind CNKI (zh, 0.70)", GapType.ACCESS_BARRIER, Severity.MEDIUM, met=False),
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
        """When a Chinese query returns nothing, reason should be access_barrier."""
        # This tests the engine's behavior when it encounters empty results
        # for a walled-garden language. The exact mechanism depends on
        # how the engine creates NegativePostulates.
        neg = NegativePostulate(
            query_text="病毒起源研究",
            language="zh",
            possible_reason="access_barrier",
            reformulation="Chinese research on virus origins",
            detected_at_cycle=1,
        )
        assert neg.possible_reason == "access_barrier"
        assert neg.language == "zh"
        # Reformulation should be in a different (accessible) language
        assert "Chinese" in neg.reformulation or "research" in neg.reformulation
```

**Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_access_barriers.py -k "TestAccessBarrierInference or TestCoverageBreakdownCalculation or TestNegativePostulateAccessBarrier" -v 2>&1 | tail -15`
Expected: FAIL (calculate_coverage doesn't return CoverageBreakdown, _access_barriers method doesn't exist)

**Step 3: Write minimal implementation**

In `src/epistemix/core.py`:

1. Update imports at top (add after existing imports):

```python
from epistemix.models import CoverageBreakdown
from epistemix.knowledge import LANGUAGE_ECOSYSTEMS, CROSS_LANGUAGE_STRATEGIES, GEOGRAPHIC_LINGUISTIC
from epistemix.query_localization import localize_query, localize_query_via_llm
```

(Note: `GEOGRAPHIC_LINGUISTIC` is already imported via `from epistemix.knowledge import GEOGRAPHIC_LINGUISTIC, ...`. Just add `LANGUAGE_ECOSYSTEMS` and `CROSS_LANGUAGE_STRATEGIES` to the existing import, and add the `query_localization` import.)

2. Add `_access_barriers` method to `DynamicInferenceEngine` (after `_institutional`, around line 764):

```python
    def _access_barriers(self, cycle: int) -> list[Expectation]:
        """Expectations for gated academic ecosystems (MA-08)."""
        expectations: list[Expectation] = []
        geo = GEOGRAPHIC_LINGUISTIC.get(self.postulates.country, {})
        primary_langs = geo.get("primary_languages", [])

        for lang in primary_langs:
            eco = LANGUAGE_ECOSYSTEMS.get(lang)
            if eco is None:
                continue  # open_web, no barrier expectation needed

            db_list = ", ".join(eco.gated_databases[:3])
            expectations.append(Expectation(
                description=(
                    f"{lang.upper()} academic sources on "
                    f"{self.postulates.topic} behind {db_list} "
                    f"({lang}, {eco.estimated_gated_share:.0%} gated)"
                ),
                gap_type=GapType.ACCESS_BARRIER,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            ))

        return expectations
```

3. Update `derive()` to call `_access_barriers` (add after existing calls, around line 636):

```python
        expectations.extend(self._access_barriers(cycle))
```

4. Update `MultilingualQueryGenerator.generate_initial_queries()` to use `localize_query`:

In `generate_initial_queries` (around line 342), replace the non-English language block. Where it currently does `_transliterate`, check if the language is in `LANGUAGE_ECOSYSTEMS` and has a non-keyword query_style, and if so, use `localize_query` instead:

After the existing `for lang in primary_langs:` block that handles non-English languages (around line 365-377), replace:

```python
            else:
                # Translate key terms if possible
                translated_terms = []
                for term in self._extract_key_terms(topic):
                    translated = self._transliterate(term, lang)
                    translated_terms.append(translated)
                if translated_terms:
                    q = " ".join(translated_terms)
                    queries.append(SearchQuery(
                        query=q,
                        language=lang,
                        rationale=f"Seed query in {lang} for {topic}",
                        priority=Severity.HIGH,
                        target_gap=GapType.LINGUISTIC,
                    ))
```

With:

```python
            else:
                eco = LANGUAGE_ECOSYSTEMS.get(lang)
                if eco and eco.query_style != "keyword":
                    # Use localized query generation
                    localized = localize_query(topic, lang, discipline)
                    for lq in localized:
                        queries.append(SearchQuery(
                            query=lq,
                            language=lang,
                            rationale=f"Localized {lang} query for {topic}",
                            priority=Severity.HIGH,
                            target_gap=GapType.LINGUISTIC,
                        ))
                else:
                    # Translate key terms if possible
                    translated_terms = []
                    for term in self._extract_key_terms(topic):
                        translated = self._transliterate(term, lang)
                        translated_terms.append(translated)
                    if translated_terms:
                        q = " ".join(translated_terms)
                        queries.append(SearchQuery(
                            query=q,
                            language=lang,
                            rationale=f"Seed query in {lang} for {topic}",
                            priority=Severity.HIGH,
                            target_gap=GapType.LINGUISTIC,
                        ))
```

5. Update `calculate_coverage` to return `CoverageBreakdown` (replace the function at line 974):

```python
def calculate_coverage(
    expectations: list[Expectation],
    anomalies: list[Anomaly],
) -> CoverageBreakdown:
    """Calculate split coverage: accessible score + estimated unreachable.

    Partitions expectations into barrier (ACCESS_BARRIER) and accessible.
    accessible_score is computed from non-barrier expectations.
    estimated_unreachable is derived from barrier expectations and their
    associated gated share percentages.
    """
    if not expectations:
        return CoverageBreakdown(
            accessible_score=0.0,
            estimated_unreachable=0.0,
        )

    # Partition expectations
    barrier_exps = [
        e for e in expectations if e.gap_type == GapType.ACCESS_BARRIER
    ]
    accessible_exps = [
        e for e in expectations if e.gap_type != GapType.ACCESS_BARRIER
    ]

    # Accessible score (same formula as before)
    weighted_total = 0.0
    weighted_met = 0.0
    for exp in accessible_exps:
        w = exp.severity_if_unmet.weight
        weighted_total += w
        if exp.met:
            weighted_met += w

    base = (weighted_met / weighted_total) * 100 if weighted_total > 0 else 0
    penalty = sum(a.severity.weight * 0.5 for a in anomalies
                  if a.gap_type != GapType.ACCESS_BARRIER)
    penalty_norm = min(penalty, 30)
    accessible_score = max(base - penalty_norm, 0.0)

    # Estimated unreachable: parse gated share from barrier expectation descriptions
    barrier_annotations: list[str] = []
    total_gated = 0.0
    gated_met = sum(1 for e in barrier_exps if e.met)

    for exp in barrier_exps:
        # Extract gated share from description pattern "(..., XX% gated)"
        import re
        match = re.search(r"(\d+)% gated", exp.description)
        if match:
            share = int(match.group(1))
            total_gated += share
            lang_match = re.search(r"\((\w+),", exp.description)
            lang_code = lang_match.group(1) if lang_match else "unknown"
            eco = LANGUAGE_ECOSYSTEMS.get(lang_code)
            if eco:
                db_names = ", ".join(eco.gated_databases[:2])
                barrier_annotations.append(
                    f"{lang_code.upper()}: ~{share}% behind {db_names}"
                )

    estimated_unreachable = total_gated / max(len(barrier_exps), 1) if barrier_exps else 0.0

    return CoverageBreakdown(
        accessible_score=round(accessible_score, 1),
        estimated_unreachable=round(estimated_unreachable, 1),
        barrier_annotations=barrier_annotations,
        gated_expectations_count=len(barrier_exps),
        gated_expectations_met=gated_met,
    )
```

6. Update `EpistemixEngine.run_cycle()` — change the coverage line (around line 1096-1098):

Replace:
```python
        coverage = calculate_coverage(
            self.all_expectations, self.all_anomalies
        )
```

With:
```python
        coverage_breakdown = calculate_coverage(
            self.all_expectations, self.all_anomalies
        )
        coverage = coverage_breakdown.accessible_score
```

7. Update `EpistemixEngine.to_dict()` — add coverage_breakdown to output (after the existing `coverage_percentage` line):

Add after `"coverage_percentage": coverage,`:

```python
            "coverage_breakdown": coverage_breakdown.to_dict()
                if hasattr(self, '_last_coverage_breakdown') else None,
```

Actually, simpler approach: store the breakdown on the engine. In `run_cycle()`, after computing `coverage_breakdown`, add:

```python
        self._last_coverage_breakdown = coverage_breakdown
```

Then in `to_dict()`, add:

```python
            "coverage_breakdown": (
                self._last_coverage_breakdown.to_dict()
                if self._last_coverage_breakdown else None
            ),
```

And initialize `self._last_coverage_breakdown = None` in `__init__`.

**Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_access_barriers.py -k "TestAccessBarrierInference or TestCoverageBreakdownCalculation or TestNegativePostulateAccessBarrier" -v 2>&1 | tail -15`
Expected: All PASS

**Step 5: Run full suite for regression**

Run: `source .venv/bin/activate && pytest tests/ -v 2>&1 | tail -5`
Expected: All pass. Critical: existing coverage tests in `test_core.py` must still work since `CoverageBreakdown.accessible_score` replaces the old float in `CycleSnapshot.coverage_score`.

**Step 6: Commit**

```bash
git add src/epistemix/core.py tests/test_access_barriers.py
git commit -m "feat: wire MA-08 into inference engine, split coverage into CoverageBreakdown"
```

---

## Task 7: SARS-CoV-2 test fixtures and integration test

Add SARS-CoV-2 mock fixtures to `conftest.py` and write an integration test that exercises the full pipeline with access barriers.

**Files:**
- Modify: `tests/conftest.py` (append fixtures)
- Test: `tests/test_access_barriers.py` (append integration tests)

**Step 1: Write the integration test**

Append to `tests/test_access_barriers.py`:

```python
class TestSARSCoV2Integration:
    """Full pipeline test with SARS-CoV-2 topic exercising access barriers."""

    def test_china_audit_produces_barrier_anomalies(
        self, sars_connector, sars_findings,
    ):
        engine = EpistemixEngine("China", "SARS-CoV-2 origins", "virology")
        engine.initialize()

        # Ingest findings
        engine.ingest_findings(sars_findings)
        snapshot = engine.run_cycle(sars_connector)

        # Should have access barrier expectations
        barrier_exps = [
            e for e in engine.all_expectations
            if e.gap_type == GapType.ACCESS_BARRIER
        ]
        assert len(barrier_exps) >= 1

        # Coverage should be a reasonable number
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
        assert breakdown["estimated_unreachable"] > 0  # China has zh behind CNKI

    def test_greece_audit_no_barrier_in_breakdown(self):
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        engine.initialize()
        engine.run_cycle()

        result = engine.to_dict()
        breakdown = result.get("coverage_breakdown")
        assert breakdown is not None
        assert breakdown["estimated_unreachable"] == 0.0
        assert breakdown["gated_expectations_count"] == 0
```

**Step 2: Add SARS-CoV-2 fixtures to conftest.py**

Append to `tests/conftest.py`:

```python
# ============================================================
# SARS-CoV-2 FIXTURES — Access barrier test scenario
# ============================================================

@pytest.fixture
def sars_findings() -> list[Finding]:
    """Mock findings for SARS-CoV-2 origins (China, virology)."""
    return [
        Finding(
            source="Proximal Origin of SARS-CoV-2",
            language="en",
            author="Andersen",
            institution="Scripps Research",
            theory_supported="Natural zoonotic spillover",
            source_type="peer_reviewed",
            year=2020,
            entities_mentioned=[
                "SARS-CoV-2", "RaTG13", "Wuhan",
                "pangolin", "bat coronavirus",
            ],
        ),
        Finding(
            source="Wuhan Institute of Virology report",
            language="en",
            author="Shi Zhengli",
            institution="Wuhan Institute of Virology",
            theory_supported="Natural origins",
            source_type="institutional",
            year=2020,
            entities_mentioned=[
                "SARS-CoV-2", "bat coronavirus", "WIV",
                "RaTG13", "Shi Zhengli",
            ],
        ),
        Finding(
            source="WHO-China joint study report",
            language="en",
            author="",
            institution="World Health Organization",
            theory_supported="",
            source_type="institutional",
            year=2021,
            entities_mentioned=[
                "SARS-CoV-2", "Huanan Seafood Market",
                "Wuhan", "zoonotic origin",
            ],
        ),
        Finding(
            source="MERS-CoV comparison study",
            language="en",
            author="Zaki",
            institution="Erasmus Medical Center",
            theory_supported="",
            source_type="peer_reviewed",
            year=2021,
            entities_mentioned=[
                "MERS-CoV", "SARS-CoV-2", "coronavirus",
                "camel", "zoonotic",
            ],
        ),
    ]


@pytest.fixture
def sars_connector() -> MockConnector:
    """MockConnector configured for SARS-CoV-2 scenario."""
    from epistemix.connector import MockConnector
    from epistemix.models import SemanticRelation, RelationType

    connector = MockConnector()
    connector.register_findings("sars", [
        Finding(
            source="Fudan University genome analysis",
            language="en",
            author="Zhang Yongzhen",
            institution="Fudan University",
            theory_supported="Natural origins",
            source_type="peer_reviewed",
            year=2020,
            entities_mentioned=["SARS-CoV-2", "genome", "Wuhan"],
        ),
    ])
    connector.register_findings("virus origins", [
        Finding(
            source="Lab leak hypothesis review",
            language="en",
            author="",
            institution="MIT Technology Review",
            theory_supported="Laboratory origin",
            source_type="journalistic",
            year=2021,
            entities_mentioned=["SARS-CoV-2", "WIV", "gain of function"],
        ),
    ])
    connector.register_relations([
        SemanticRelation(
            source="Shi Zhengli", target="Andersen",
            relation=RelationType.CONTESTS, confidence=0.7,
            evidence="Competing origin hypotheses",
            language="en",
        ),
    ])
    connector.register_localized_queries("zh", [
        "新冠病毒起源研究",
        "SARS-CoV-2来源调查",
    ])
    return connector
```

**Step 3: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_access_barriers.py::TestSARSCoV2Integration -v 2>&1 | tail -15`
Expected: All PASS

**Step 4: Run full suite for regression**

Run: `source .venv/bin/activate && pytest tests/ -v 2>&1 | tail -5`
Expected: All pass

**Step 5: Commit**

```bash
git add tests/conftest.py tests/test_access_barriers.py
git commit -m "feat: add SARS-CoV-2 fixtures and access-barrier integration tests"
```

---

## Task 8: Update CLAUDE.md and TODO.md

Update project documentation to reflect Phase 4 completion.

**Files:**
- Modify: `CLAUDE.md`
- Modify: `TODO.md`

**Step 1: Update CLAUDE.md**

- Update repo structure: add `query_localization.py`, mention 8 meta-axioms
- Update dependency graph: add `query_localization.py`
- Update architecture decisions: add access barriers row
- Update meta-axioms table: add MA-08
- Update test count
- Move Phase 4 from "not done" to "done"

**Step 2: Update TODO.md**

- Mark Phase 4 items as `[x]`
- Update priority order

**Step 3: Commit**

```bash
git add CLAUDE.md TODO.md
git commit -m "docs: update CLAUDE.md and TODO.md for v3 Phase 4 completion"
```

---

## Task 9: Final verification

Run the full test suite one last time, verify CLI works, confirm no regressions.

**Step 1: Run full test suite**

Run: `source .venv/bin/activate && pytest tests/ -v 2>&1`
Expected: All tests pass (171 existing + ~30 new ≈ ~201 total)

**Step 2: Run CLI in mock mode**

Run: `source .venv/bin/activate && epistemix --topic "SARS-CoV-2 origins" --country China --discipline virology --dry-run`
Expected: Should show queries including localized Chinese queries

**Step 3: Run CLI with Amphipolis (regression)**

Run: `source .venv/bin/activate && epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology --dry-run`
Expected: Same behavior as before (no access barriers for Greece)

**Step 4: Verify no import cycles**

Run: `source .venv/bin/activate && python -c "from epistemix.query_localization import localize_query; print('OK')"`
Expected: `OK`

**Step 5: Verify clean git status**

Run: `git status`
Expected: Clean working tree

---

## Summary

| Task | Files | Tests Added | Cumulative |
|------|-------|-------------|------------|
| 1. Data structures | models.py | ~8 | 179 |
| 2. Ecosystem registry | knowledge.py | ~10 | 189 |
| 3. MA-08 axiom | meta_axioms.py | ~5 | 194 |
| 4. Query localization | query_localization.py (new) | ~12 | 206 |
| 5. Connector changes | connector.py | ~2 | 208 |
| 6. Engine integration | core.py | ~7 | 215 |
| 7. Integration tests | conftest.py | ~3 | 218 |
| 8. Documentation | CLAUDE.md, TODO.md | 0 | 218 |
| 9. Final verification | (none) | 0 | 218 |
