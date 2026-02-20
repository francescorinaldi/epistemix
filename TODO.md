# TODO — Epistemix Roadmap

## Status Key

- [x] Done
- [ ] Not started
- [~] In progress

---

## Phase 1: Core Library (COMPLETE)

- [x] `models.py` — Data structures (Finding, Postulate, Anomaly, Query, CoverageScore, ResearchState)
- [x] `meta_axioms.py` — 7 Level 0 meta-axioms with postulate templates
- [x] `citation_graph.py` — BFS school detection, citation islands, priority ranking
- [x] `disciplines.py` — Evidence→discipline mapping, gap detection
- [x] `content_analysis.py` — Structural absence, convergence, empty query analysis
- [x] `connector.py` — MockConnector + ClaudeConnector
- [x] `core.py` — EpistemicEngine (postulates, queries, ingestion, coverage, anomalies, cycles)
- [x] `multi_agent.py` — Agent α/β + Arbiter + MultiAgentSystem
- [x] `run.py` — CLI with all flags
- [x] 113 tests (all passing)
- [x] `pyproject.toml` — Package configuration, entry point

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

## Phase 5: Enhanced Features (NOT STARTED)

- [ ] **PDF report generation** — Downloadable audit report with charts and findings
- [ ] **JSON export** — Full audit data as structured JSON download
- [ ] **Audit comparison** — Compare two audits side-by-side
- [ ] **Audit sharing** — Public URL for sharing audit results
- [ ] **Custom axiom templates** — Per-discipline axiom sets (medicine, finance, law)
- [ ] **Team features** — Organizations with shared audits
- [ ] **Audit history diffing** — Show what changed between cycles
- [ ] **Interactive anomaly resolution** — Mark anomalies as resolved with notes

## Phase 6: Scale & Polish (NOT STARTED)

- [ ] **Rate limiting** — API rate limits per plan tier
- [ ] **Caching** — Cache similar queries to reduce API calls
- [ ] **Monitoring** — Sentry for errors, Vercel Analytics for usage
- [ ] **Onboarding flow** — Interactive tutorial for first-time users
- [ ] **Mobile responsiveness** — Ensure all components work on mobile
- [ ] **Accessibility** — ARIA labels, keyboard navigation
- [ ] **i18n** — Interface localization (at minimum: English, Italian, Greek)
- [ ] **SEO** — Meta tags, Open Graph, structured data

## Phase 7: Advanced Research Features (FUTURE)

- [ ] **Temporal analysis** — Track how coverage of a topic evolves over months/years
- [ ] **Cross-topic comparison** — Compare epistemic coverage across topics
- [ ] **Citation graph visualization** — Full interactive graph in the browser (larger scale)
- [ ] **Automated follow-up audits** — Re-run audits periodically and alert on changes
- [ ] **Domain-specific evidence maps** — Medicine: clinical trials, case studies, meta-analyses
- [ ] **LLM-assisted anomaly interpretation** — Use Claude to explain why anomalies matter
- [ ] **Collaborative audits** — Multiple users contribute findings to the same audit

---

## Known Issues

- Web app `npm install` not yet run (no `node_modules/` or `package-lock.json`)
- No end-to-end test with live Claude API (only MockConnector tested)
- Entity extraction regex patterns may miss non-Latin names
- `EVIDENCE_DISCIPLINE_MAP` is archaeology-focused — needs expansion for other fields
- Worker Dockerfile not yet tested in production Fly.io environment

---

## Priority Order

For the next development session, the recommended order is:

1. **Deploy to Supabase/Vercel/Fly.io** (Phase 3) — Get it running for real
2. **Run one live audit** — Test with real Claude API to validate entity extraction
3. **Stripe billing** — Minimum viable: Pro plan checkout + webhook
4. **PDF reports** — Most requested feature for sharing results
5. **Custom axiom templates** — Needed to expand beyond archaeology
