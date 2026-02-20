# Epistemix Implementation Plan

## Overview

Build the complete Epistemix Epistemic Audit Framework — a system for detecting "unknown unknowns" in research by predicting what knowledge should exist, then verifying whether it does.

**Target:** ~170KB of Python across 9 source files + 2 test files, Python 3.10+, no external deps beyond `anthropic` (optional, for live use).

---

## Project Structure

```
epistemix/
├── README.md
├── pyproject.toml
├── .gitignore
├── src/
│   └── epistemix/
│       ├── __init__.py              # Package exports, version
│       ├── models.py                # All data models (Finding, Postulate, Anomaly, Query, etc.)
│       ├── meta_axioms.py           # Level 0 meta-axioms (fixed structural knowledge)
│       ├── core.py                  # Main engine (~46KB) — postulates, queries, cycles, coverage
│       ├── citation_graph.py        # Citation graph analysis (~11KB) — schools, islands
│       ├── disciplines.py           # Disciplinary expectations (~12KB) — evidence→discipline rules
│       ├── content_analysis.py      # Content analysis (~17KB) — absences, convergence, empty queries
│       ├── multi_agent.py           # Dual-agent system (~24KB) — α/β agents + arbiter
│       ├── connector.py             # API connector (~13KB) — MockConnector + ClaudeConnector
│       └── run.py                   # CLI orchestrator (~12KB)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures, mock data
│   ├── test_models.py
│   ├── test_core.py
│   ├── test_citation_graph.py
│   ├── test_disciplines.py
│   ├── test_content_analysis.py
│   ├── test_multi_agent.py
│   ├── test_connector.py
│   ├── test_integrated.py           # Full integration test (~17KB)
│   └── test_amphipolis.py           # Amphipolis 4-cycle simulation (~21KB)
```

**Key design decision:** A separate `models.py` centralizes all data structures to prevent circular imports and ensure a clean DAG dependency graph.

---

## Implementation Phases (in order)

### Phase 1: Foundation
Files: `pyproject.toml`, `.gitignore`, `__init__.py`, `models.py`, `meta_axioms.py`, `tests/conftest.py`, `tests/test_models.py`

1. **pyproject.toml** — Python 3.10+, no mandatory deps, optional `anthropic` for live use, pytest for dev
2. **models.py** — All data structures using `dataclasses` + `enum`:
   - `Severity` (CRITICAL/HIGH/MEDIUM), `FindingType`, `PostulateStatus`, `AnomalyType`, `QueryLanguage`
   - `Finding` — discovered entity (scholar, theory, institution, etc.) with dedup via `__hash__`/`__eq__`
   - `Postulate` — dynamic assertion about what should exist, with status tracking
   - `Anomaly` — gap between expectation and finding, with severity and suggested queries
   - `Query` — search query with language, priority, execution status
   - `CoverageScore` — always a lower bound (confirmed/total postulates + anomaly counts)
   - `ResearchState` — complete audit state container (findings, postulates, anomalies, queries, coverage history)
3. **meta_axioms.py** — 7 Level 0 meta-axioms (language, institution, theory, school, discipline, publication, temporal)
4. **Tests** for models and fixtures

### Phase 2: Analysis Modules
Files: `citation_graph.py`, `disciplines.py`, `content_analysis.py` + their tests

5. **citation_graph.py** — `CitationGraph` class:
   - Directed adjacency list (no networkx)
   - `detect_schools()` — mutual citation clusters via BFS connected components
   - `check_single_school()` → CRITICAL anomaly if only one school
   - `find_citation_islands()` — scholars cited by many but never directly searched
   - `investigation_priority_ranking()` — priority = in_citations / (direct_searches + 1)

6. **disciplines.py** — `DisciplineExpectations` class:
   - `EVIDENCE_DISCIPLINE_MAP`: inscriptions→epigraphy, human_remains→osteology, mosaics→art_history, etc.
   - `register_evidence()` → generates postulates for expected disciplines
   - `detect_anomalies()` → flags when evidence found but no specialist
   - Target: identify 3 Amphipolis gaps (epigraphy, osteology, art history)

7. **content_analysis.py** — Three analyzers + facade:
   - `StructuralAbsenceAnalyzer`: N entities found, M discussed → N-M gaps
   - `ConvergenceAnalyzer`: uniformity score, excess convergence/divergence detection
   - `EmptyQueryAnalyzer`: patterns in queries that returned nothing
   - `ContentAnalysisEngine`: facade combining all three

### Phase 3: Core Engine + Connector
Files: `connector.py`, `core.py` + their tests

8. **connector.py** — `BaseConnector` (ABC), `MockConnector`, `ClaudeConnector`:
   - `MockConnector`: pattern-matched canned responses, call logging
   - `ClaudeConnector`: Anthropic SDK with `web_search_20250305` tool, budget tracking, rate limiting, retry with backoff, structured JSON parsing

9. **core.py** — `EpistemicEngine` (the largest module):
   - **Postulate management**: `initialize_postulates()` from meta-axioms + (topic, country, discipline)
   - **Query generation**: `generate_initial_queries()` multilingual, `generate_queries_from_anomalies()` targeted
   - **Multilingual support**: language-country mapping table, template-based query translation with pre-built term lookup tables (Greek, French, German, Italian for archaeology domain)
   - **Result ingestion**: `ingest_results()` → extract entities → deduplicate → link to queries
   - **Postulate updating**: findings confirm postulates; new evidence types generate new postulates dynamically
   - **Coverage calculation**: always framed as lower bound (confirmed/total, denominator grows)
   - **Anomaly detection**: language gaps, theory gaps, discipline gaps, institution gaps
   - **Cycle orchestration**: `run_cycle()` and `run_all_cycles()` with convergence check

### Phase 4: Multi-Agent + Integration Tests
Files: `multi_agent.py`, `test_integrated.py`, `test_amphipolis.py`

10. **multi_agent.py** — Dual-agent epistemic audit:
    - `AgentPerspective` — axiom weight configuration
    - `EpistemicAgent` — generates weighted postulates, evaluates findings, detects anomalies from its perspective
    - Agent α (institutional): weights MA-01/02/04/06 → institutions, languages, schools, publications
    - Agent β (theoretical): weights MA-03/05/07 → theories, disciplines, temporal
    - `Arbiter` — compares reports, finds agreement/disagreement, promotes discrepancies to known unknowns
    - `MultiAgentSystem` — orchestrator, combined coverage = min(α, β)
    - Target: α=71% 0 anomalies, β=67% 5 anomalies, combined=54%, blindness=21 points

11. **test_integrated.py** — Full pipeline test with all modules using MockConnector
12. **test_amphipolis.py** — 4-cycle simulation with carefully crafted mock data:
    - Cycle 0: 1 scholar, 1 theory, ~38% coverage
    - Cycle 1: 6 scholars, 3 theories, ~57%, Mavrogiannis flagged as gap
    - Cycle 2: 8 scholars, 4 theories, ~69%, Mavrogiannis found
    - Cycle 3: 11 scholars, 4 theories, ~75%
    - Multi-agent: 18 anomalies (2 CRITICAL, 9 HIGH, 7 MEDIUM)

### Phase 5: CLI + README
Files: `run.py`, updated `README.md`

13. **run.py** — CLI entry point:
    - `--topic`, `--country`, `--discipline` (required)
    - `--cycles` (default 4), `--live`/`--mock`, `--verbose`, `--output`, `--budget`, `--model`
    - Progress display, anomaly summary, final report as JSON

14. **README.md** — Project documentation with usage examples

---

## Dependency Graph (strict DAG, no cycles)

```
meta_axioms.py ──┐
                 │
models.py ───────┤
                 ├──► citation_graph.py ──┐
                 ├──► disciplines.py ─────┤
                 ├──► content_analysis.py ┤
                 │                        │
                 ├──► connector.py        │
                 │       │                │
                 │       ▼                ▼
                 └──► core.py ──────► multi_agent.py
                                          │
                                          ▼
                                       run.py
```

---

## Key Amphipolis Test Targets

| Metric | Target |
|--------|--------|
| Cycle 0 coverage | ~38% |
| Cycle 1 coverage | ~57% |
| Cycle 2 coverage | ~69% |
| Cycle 3 coverage | ~75% |
| Multi-agent coverage | ~54% |
| Blindness gap | ~21 points |
| Total unique anomalies | 18 |
| CRITICAL anomalies | 2 |
| HIGH anomalies | 9 |
| MEDIUM anomalies | 7 |

---

## Commit Strategy

One commit per phase, pushed to `claude/epistemix-planning-2bRZx`:
1. "Add project scaffolding, data models, and meta-axioms"
2. "Add analysis modules: citation graph, disciplines, content analysis"
3. "Add core engine and API connector"
4. "Add multi-agent system and integration tests"
5. "Add CLI orchestrator and documentation"
