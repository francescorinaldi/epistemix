# Epistemix Development Plan

## Current State (v0.2.0 — Feb 2026)

**Core library:** 10 Python modules, 105 tests passing, zero external deps.
**Production stack:** Next.js 15 web app, Fly.io worker, Supabase database, CI/CD.
**Live test:** Validated on Antikythera mechanism (Opus 4.6 Extended, Feb 20 2026).
**Copilot review:** 9 production bugs fixed (RLS, billing, worker imports, etc).

### Live Test Results (Antikythera Mechanism)

The first live test with Claude web search confirmed the core thesis:
**monolingual coverage creates an illusion of completeness.**

Key findings:
- ~85% of principal scholars found with English-only coverage
- 5 specific gaps invisible to monolingual search:
  - Swiss excavation campaign (French sources)
  - Italian school: Pastore, Rossi (Italian sources)
  - Skeptical voice: Lequèvre (French critique)
  - Olbia mechanism predecessor (French sources)
  - Arab-Islamic and Chinese transmission traditions
- Cycle 3 queries were surgical: Arabic on al-Biruni, Chinese on ancient
  astronomical instruments, Italian on Pastore, French on Lequèvre
- **Cycle 4 spontaneously generated domain-specific axioms** not in the 7 meta-axioms:
  - Disciplinary axiom: "where are the metallurgists, mechanical engineers?"
  - Access axiom: "who controls physical access to the fragments?"
  - Predecessor axiom: "too sophisticated to be a first attempt — where are predecessors?"
  - Social context axiom: "for whom was it built? economic/political role?"
  - Competing reconstructions axiom: "how many models exist, where do they diverge?"
  - Babylonian axiom: "the cycles are Babylonian — who studies the transmission?"

This last observation — the LLM generating novel axioms — validates Phase 8 (auto-audit)
as a natural capability, not just a theoretical idea.

---

## v3 Roadmap (8 Phases)

### Conceptual Leap: v2 → v3

| Dimension | v2 | v3 |
|-----------|----|----|
| Postulates | Dynamic, auto-discovered | Relational + confidence + decay |
| Entities | Discovered by keyword | Extracted with semantic relations |
| Time | None | Temporal evolution, decay |
| Memory | None | Cross-session persistence |
| Languages | en, el, de, fr, it | + ar, zh + access-barrier axioms |
| Multi-agent | 2 fixed agents | N agents, generative axioms |
| Auto-audit | None | System audits its own axioms |

---

### Phase 1: Weighted Postulates (confidence scores)

**Priority:** HIGH — Foundation for phases 2, 5, 7.
**Effort:** Small — extend `DynamicPostulates` in `core.py`.
**Depends on:** Nothing.

Add `WeightedPostulate` with confidence scoring:
- `confidence: float` (0.0–1.0) based on source count, language spread, recency, authority
- `source_count`, `language_spread`, `last_confirmed`
- Retrofit: every v2 postulate becomes weighted with confidence=0.5

Confidence thresholds drive query strategy:
- < 0.2: VERIFICA — generate confirmation/refutation queries
- 0.2–0.6: STANDARD — normal expectations
- 0.6–0.9: AFFIDABILE — generate deepening queries
- > 0.9: CONSOLIDATO — quasi-fact, strong constraint

**Test:** Amphipolis postulates should reach different confidence levels.
Peristeri (many sources, multiple languages) → high confidence.
Dendrinos (single source) → low confidence, triggers verification query.

---

### Phase 2: Negative Postulates (query-void feedback loop)

**Priority:** HIGH — currently content_analysis detects empty queries but doesn't feed back.
**Effort:** Small — extend `content_analysis.py`, wire to `DynamicPostulates`.
**Depends on:** Nothing.

When a query returns zero results, generate a `NegativePostulate`:
- `query`, `language`, `expected_by` (which axiom), `attempts`
- `possible_reasons`: access_barrier, genuinely_absent, wrong_terminology, wrong_language
- Reasons are tested in subsequent cycles with reformulated queries

**Test:** German query on Amphipolis returning nothing → generates NegativePostulate →
next cycle reformulates with alternative terminology.

---

### Phase 3: Semantic Relation Graph

**Priority:** HIGH — the qualitative leap. Replaces `citation_graph.py`.
**Effort:** Large — new `semantic_graph.py`, LLM extraction prompts in connector.
**Depends on:** Connector changes for relation extraction.

New `RelationType` enum: SUPPORTS, CONTESTS, CITES, EXTENDS, SUPERVISES, COAUTHORS.

`SemanticRelation` dataclass: source, target, relation, confidence, evidence, timestamp.

Extraction via LLM: for each finding, Claude extracts relationships with evidence quotes.

Automated inferences from the typed graph:
- Schools of thought = clusters of mutual SUPPORTS
- Lines of fracture = CONTESTS pairs
- Authority = high in-degree CITES nodes
- Isolation = scholars with no relations (independent voices or gaps)
- Influence chains = A supervises B, B extends C

Coverage v3 includes a relational component: not enough to find 10 scholars;
must verify their relationships are mapped. Unmapped pairs get flagged.

**Test:** Amphipolis graph should distinguish Mavrogiannis-contests-Peristeri
from Chugg-cites-Peristeri. Tiverios should appear as an isolated voice.

---

### Phase 4: Arabic + Chinese with Access-Barrier Axioms

**Priority:** MEDIUM — validated by live test (Antikythera showed the need).
**Effort:** Medium — extend `core.py` + `QueryLanguage` enum + new `AccessBarrierAxiom`.
**Depends on:** Phase 2 (negative postulates needed for barrier detection).

New `AccessBarrierAxiom` per language:
- `ecosystem`: open_web, walled_garden, hybrid
- `primary_databases`: CNKI/Wanfang for zh, Shamaa/E-Marefa for ar
- `searchable_via_google`: 0.25 for zh, 0.5 for ar
- `bilingual_pattern`: ar has ar_local/en_international

Impact on coverage: zero results in walled_garden ecosystem → annotate
"coverage not evaluable via web search" instead of penalizing.

Query generation adaptations:
- Chinese: natural phrases (no word-separated keywords)
- Arabic: include morphological variants (triliteral roots)

**Test:** Audit on a topic with strong Chinese component (e.g., SARS-CoV-2 origins).

---

### Phase 5: Cross-Session Memory (`knowledge_store.py`)

**Priority:** MEDIUM — the moat. Accumulated axioms are the defensible asset.
**Effort:** Medium — new persistence module + schema.
**Depends on:** Phases 1-2.

Persistent artifacts per domain:
- Level 1 axioms discovered
- Relation graph (accumulated)
- Negative postulates (confirmed)
- Calibrations (thresholds, decay rate, weights)
- Session history

Warm start: new audit on a known domain loads pre-existing axioms,
graph, and calibrations. Cycle 0 starts from a base, not from zero.

Cross-domain transfer: axioms transferable between similar domains
with low initial confidence (0.3), must be verified in first cycle.
E.g., archaeology Greece → archaeology Egypt: "national school pattern" hypothesis.

Storage: SQLite for dev, Supabase/PostgreSQL for production.

**Test:** Run Amphipolis audit, then Antikythera audit.
Second audit should start with archaeological axioms already known.

---

### Phase 6: Generative Multi-Agent

**Priority:** LOW — ambitious, needs phases 1-3 first.
**Effort:** Large — LLM-dependent agent generation.
**Depends on:** Phase 3 (semantic graph), Phase 1 (confidence).

`AgentFactory`: when α and β agree on a gap but diverge on cause,
generate a third agent with LLM-designed axioms for that divergence.

`MetaPostulate`: when discrepancy persists after third agent,
explicit declaration that current axioms are insufficient.
Suggests external intervention type: domain expert review,
primary source access, field research required.

Limit: max 1 generated agent per session (cost control).

**Test:** Amphipolis — when α and β diverge on the occupant question,
generate a "forensic evidence" agent focused on osteological data.

---

### Phase 7: Temporal Decay

**Priority:** HIGH — very small once Phase 1 exists.
**Effort:** Small — add decay to `WeightedPostulate`.
**Depends on:** Phase 1.

`decay_rate: float` (per month), configurable by domain:
- Archaeology: 0.02 (slow, knowledge changes slowly)
- Finance: 0.15 (fast, markets change rapidly)
- Virology: 0.10 (moderate, new findings frequent)

`effective_confidence(now)` = confidence × (1 - decay_rate) ^ months_since_last_confirmed

Postulates not confirmed by recent sources lose influence.
They don't disappear — they become weak hypotheses.

**Test:** A postulate last confirmed in 2020 should have noticeably
lower effective confidence than one confirmed in 2025.

---

### Phase 8: Auto-Audit of Axioms

**Priority:** LOW — the most innovative and riskiest module. Last to implement.
**Effort:** Large — requires all previous phases.
**Depends on:** All above.

After each complete audit, run an additional cycle:
"My meta-axioms assume knowledge in [domain] organizes by institutions,
languages, schools, and subdisciplines. Is this correct for [domain]?
Are there organizational dimensions I'm not considering?"

If LLM identifies a missing dimension (confidence > 0.7):
generate new expectation axis, re-run audit including it.

The Antikythera live test already demonstrated this naturally:
Claude spontaneously generated the "Babylonian transmission" axiom,
the "predecessor" axiom, and the "access control" axiom.
Phase 8 formalizes what the LLM already does intuitively.

Limits: max 2 auto-audit cycles per session.
Discovered dimensions saved as hypotheses in knowledge store,
not as confirmed axioms.

---

## Implementation Priority

The founder's sequencing is clear:

```
Phase 1 (confidence) ──┬── Phase 7 (decay)     ← Week 1
Phase 2 (negatives)  ──┘
                        ├── Phase 4 (ar/zh)     ← Week 2-3
                        ├── Phase 5 (memory)    ← Week 3-4
Phase 3 (relations)  ────── Phase 6 (gen agent) ← Week 4-6
                        └── Phase 8 (auto-audit)← After validation
```

**Immediate (this session or next):** Phases 1 + 2 + 7
**Short-term:** Phases 3 + 4
**Medium-term:** Phase 5 (the moat)
**After validation:** Phases 6 + 8

---

## Defensibility Architecture

The moat is built on three pillars:

1. **Axiom library** (grows with use) — accumulated domain axioms are proprietary.
   After 100 audits on 50 domains, a competitor must rebuild from scratch.

2. **Academic publication** — the paper establishes intellectual priority.
   Structure: (1) problem, (2) formal framework, (3) experimental results
   (Amphipolis + Antikythera), (4) limits, (5) AGI implications.
   Target: AAAI, NeurIPS workshop, or AI/epistemology journal.

3. **Domain verticals** — months of specialized work per domain:
   - Medicine: Cochrane Reviews, PubMed/CNKI/LILACS, evidence levels
   - Finance: corporate registries, due diligence structure, regulatory sources
   - Intelligence: OSINT classification, linguistic asymmetries, disinfo patterns
   - Law: jurisprudence by legal family, primary sources by jurisdiction

**Licensing:**
- Core framework: MIT (attracts community, establishes authorship)
- Knowledge store: proprietary, not distributed
- Verticals: commercial license
- Reports: watermarked for traceability

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API cost explosion | Relation extraction + generative agents = 2-3x calls | Cache aggressively. Haiku for extraction. Budget cap. Batch calls. |
| LLM hallucinations | Invented relations pollute the graph | Require evidence (textual quote). No evidence = confidence 0.1. |
| Auto-audit loops | System never converges | Hard limit: 2 auto-audit cycles. Convergence threshold = stop. |
| Knowledge store pollution | Wrong axioms persist, degrade future audits | Confidence scores. Periodic review. Domain-level reset. |
| Over-engineering | Building v3 before validating v2 live | FIRST the live test of v2. ✅ Done — Antikythera test passed. |

---

## Dependency Graph (v3)

```
models.py ───────────────────────────────────────────────┐
   │                                                     │
meta_axioms.py ──┐                                       │
                 │                                       │
   ├─► citation_graph.py ──┐   (v2, replaced by ↓ in v3)│
   │                       │                             │
   ├─► semantic_graph.py ──┤   (v3, Phase 3)             │
   │                       │                             │
   ├─► disciplines.py ─────┤                             │
   │                       │                             │
   ├─► content_analysis.py ┤                             │
   │                       │                             │
   ├─► connector.py        │                             │
   │       │               │                             │
   │       ▼               ▼                             │
   └─► core.py ──────► multi_agent.py                    │
           │               │                             │
           ▼               ▼                             │
       knowledge_store.py  (v3, Phase 5)                 │
           │                                             │
           ▼                                             │
        run.py ◄─────────────────────────────────────────┘
```

**Rule:** Never import upward. `knowledge_store.py` reads from `core.py`
and `multi_agent.py` but does not feed back into them at import time.
