# TODO — Epistemix Roadmap

## Status Key

- [x] Done
- [ ] Not started
- [~] In progress

---

## Phase 1: Core Library (COMPLETE)

- [x] `models.py` — Data structures (Finding, Postulate, Anomaly, Query, CoverageScore, ResearchState)
- [x] `meta_axioms.py` — 7 Level 0 meta-axioms with postulate templates
- [x] `citation_graph.py` → `semantic_graph.py` — Typed relation graph, school/fracture detection
- [x] `disciplines.py` — Evidence→discipline mapping, gap detection
- [x] `content_analysis.py` — Structural absence, convergence, empty query analysis
- [x] `connector.py` — MockConnector + ClaudeConnector
- [x] `core.py` — EpistemicEngine (postulates, queries, ingestion, coverage, anomalies, cycles)
- [x] `multi_agent.py` — Agent α/β + Arbiter + MultiAgentSystem
- [x] `run.py` — CLI with all flags
- [x] `pyproject.toml` — Package configuration, entry point

## Phase 1b: v3 Foundations (COMPLETE)

- [x] `WeightedPostulate` — Confidence scoring (0.0–1.0) with temporal decay
- [x] `NegativePostulate` — Structured evidence of absence with reformulation
- [x] Confidence-driven query generation (VERIFY / DEEPEN strategies)
- [x] Empty query → NegativePostulate feedback loop
- [x] Temporal decay per domain (archaeology: 0.02, finance: 0.15)
- [x] CycleSnapshot v3 fields (weighted_postulates_count, avg_confidence, negative_postulates_count)
- [x] Engine serialization includes v3 data
- [x] 171 tests (all passing)

## Phase 2: Production Stack (COMPLETE — code written, not yet deployed)

- [x] Supabase schema — 4 migrations (profiles, audits, findings, billing)
- [x] Row Level Security — Policies on all tables
- [x] Database triggers — Auto-create profile, notify new audit, increment count
- [x] Supabase Realtime — Enabled on audits table
- [x] Edge Function — `trigger-worker` starts Fly.io machine on INSERT
- [x] Worker — `main.py` + `supabase_writer.py` + Dockerfile + fly.toml
- [x] Next.js web app — Layout, landing, auth, dashboard, new audit, live audit
- [x] API routes — POST/GET /api/v1/audits, GET/POST /api/v1/audits/:id
- [x] React components — CoverageChart, AnomalyPanel, CitationGraph, CycleTimeline, BlindnessGauge, AuditForm
- [x] Realtime hooks — useAuth, useAuditRealtime
- [x] Docker Compose — Local development setup
- [x] CI/CD — GitHub Actions (test, deploy-web, deploy-worker)

## Phase 3: Deployment & Go-Live (NOT STARTED)

- [ ] **Create Supabase project** — Run migrations, configure auth providers
- [ ] **Deploy web to Vercel** — Connect repo, set env vars, first deploy
- [ ] **Deploy worker to Fly.io** — Create app, deploy Docker image
- [ ] **Configure webhooks** — Supabase webhook → Edge Function on audit INSERT
- [ ] **DNS and domain** — Custom domain for the web app
- [ ] **Environment variables** — All secrets set in Vercel/Fly.io/Supabase
- [ ] **Smoke test** — End-to-end test with a real audit (live Claude API)

## Phase 4: Billing & Business (NOT STARTED)

- [ ] **Stripe integration** — Customer creation, checkout session, webhook
- [ ] **Subscription management** — Pro plan purchase/cancel/upgrade
- [ ] **Usage metering** — Track audits per user, enforce limits in real-time
- [ ] **BYOK UI** — Settings page for users to enter their Anthropic API key
- [ ] **API key management** — Enterprise customers get API keys for programmatic access
- [ ] **Plan upgrade prompts** — In-app prompts when free tier limits reached

## v3 Phase 3: Semantic Relation Graph (COMPLETE)

- [x] **RelationType enum** — SUPPORTS, CONTESTS, CONTRADICTS, CITES, EXTENDS, SUPERVISES, COAUTHORS, TRANSLATES
- [x] **SemanticRelation dataclass** — source, target, relation, confidence, evidence, language, cycle
- [x] **semantic_graph.py** — Replaces citation_graph.py (449 lines, 7 detectors, 36 tests)
- [x] **LLM relation extraction** — extract_relations() in BaseConnector, MockConnector, ClaudeConnector
- [x] **Automated inference** — Schools = SUPPORTS union-find, fractures = CONTESTS/CONTRADICTS, influence = DFS chains
- [x] **Engine integration** — run_cycle(connector=None), incremental extraction, backward compatible

## v3 Phase 4: Arabic + Chinese Access Barriers (NOT STARTED)

- [ ] **AccessBarrierAxiom** — Per-language ecosystem classification (open_web, walled_garden)
- [ ] **Chinese query generation** — Natural phrases, no word-separated keywords
- [ ] **Arabic query generation** — Morphological variants, triliteral roots
- [ ] **Coverage annotation** — "not evaluable via web search" for walled-garden languages
- [ ] **Test with SARS-CoV-2 or similar topic** with strong Chinese research component

## v3 Phase 5: Cross-Session Memory (NOT STARTED)

- [ ] **knowledge_store.py** — Persistence module for accumulated axioms
- [ ] **Domain axiom library** — Level 1 axioms discovered from audits
- [ ] **Warm start** — New audit on known domain loads pre-existing axioms
- [ ] **Cross-domain transfer** — Axioms transferable between similar domains (low initial confidence)
- [ ] **Storage backend** — SQLite for dev, Supabase for production

## v3 Phase 6: Generative Multi-Agent (NOT STARTED)

- [ ] **AgentFactory** — Generate third agent when α/β diverge
- [ ] **MetaPostulate** — Explicit "axioms insufficient" declaration
- [ ] **Cost control** — Max 1 generated agent per session
- [ ] **External intervention types** — Domain expert review, primary source access

## v3 Phase 8: Auto-Audit of Axioms (NOT STARTED)

- [ ] **Axiom self-evaluation** — After audit, ask "are my meta-axioms correct for this domain?"
- [ ] **New dimension discovery** — If LLM identifies missing dimension (conf > 0.7), add it
- [ ] **Hard limits** — Max 2 auto-audit cycles per session
- [ ] **Hypothesis storage** — Save discovered dimensions in knowledge store as hypotheses

## Production: Enhanced Features (NOT STARTED)

- [ ] **PDF report generation** — Downloadable audit report with charts and findings
- [ ] **JSON export** — Full audit data as structured JSON download
- [ ] **Audit comparison** — Compare two audits side-by-side
- [ ] **Audit sharing** — Public URL for sharing audit results
- [ ] **Custom axiom templates** — Per-discipline axiom sets (medicine, finance, law)
- [ ] **Team features** — Organizations with shared audits

## Production: Scale & Polish (NOT STARTED)

- [ ] **Rate limiting** — API rate limits per plan tier
- [ ] **Caching** — Cache similar queries to reduce API calls
- [ ] **Monitoring** — Sentry for errors, Vercel Analytics for usage
- [ ] **i18n** — Interface localization (at minimum: English, Italian, Greek)

---

## Known Issues

- Web app `npm install` not yet run (no `node_modules/` or `package-lock.json`)
- Entity extraction regex patterns may miss non-Latin names
- `EVIDENCE_DISCIPLINE_MAP` is archaeology-focused — needs expansion for other fields
- Worker Dockerfile not yet tested in production Fly.io environment

---

## Priority Order

For the next development session, the recommended order is:

1. ~~**v3 Phase 3: Semantic Relation Graph**~~ — DONE (PR #4, merged Feb 2026)
2. **v3 Phase 4: Arabic + Chinese** — Validated by live test (Antikythera showed need)
3. **v3 Phase 5: Cross-Session Memory** — The moat (accumulated axioms are the defensible asset)
4. **Deploy to Supabase/Vercel/Fly.io** — Get production stack running
5. **Stripe billing** — Minimum viable: Pro plan checkout + webhook
6. **Academic paper** — Amphipolis + Antikythera experimental results → AAAI/NeurIPS target
