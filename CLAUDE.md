# CLAUDE.md — Project Context for Claude Instances

This file is read automatically by Claude Code when opening this repository.
It provides the essential context needed to understand, modify, and extend Epistemix.

## What is Epistemix?

Epistemix is an **epistemic audit framework** that detects "unknown unknowns" in research. Given a topic, country, and discipline, it:

1. Predicts what knowledge *should* exist (via 7 meta-axioms)
2. Generates multilingual search queries
3. Extracts entities (scholars, institutions, theories, evidence)
4. Detects anomalies (missing languages, absent disciplines, citation islands)
5. Runs a dual-agent audit (two agents with different biases → an arbiter finds where they disagree)
6. Reports coverage as a lower bound — we can never be sure we found everything

The reference scenario is the **Amphipolis tomb excavation** (Greece, archaeology). All mock data and test fixtures use this scenario.

## Repository Structure

```
epistemix/
├── src/epistemix/           # Core Python library (THE BRAIN)
│   ├── models.py            # All data structures (Finding, Postulate, Anomaly, etc.)
│   ├── meta_axioms.py       # 7 Level 0 meta-axioms
│   ├── citation_graph.py    # BFS school detection, citation islands
│   ├── disciplines.py       # Evidence → expected discipline mapping
│   ├── content_analysis.py  # Structural absence, convergence, empty query patterns
│   ├── connector.py         # MockConnector (tests) / ClaudeConnector (production)
│   ├── core.py              # EpistemicEngine — main audit orchestrator
│   ├── multi_agent.py       # Dual-agent α/β + arbiter
│   └── run.py               # CLI entry point
│
├── tests/                   # 113 tests (pytest)
│   ├── conftest.py          # Shared fixtures, Amphipolis mock data
│   ├── test_models.py       # Data structure tests
│   ├── test_citation_graph.py
│   ├── test_disciplines.py
│   ├── test_content_analysis.py
│   ├── test_connector.py
│   ├── test_core.py         # EpistemicEngine tests
│   ├── test_multi_agent.py
│   ├── test_integrated.py   # Full pipeline integration test
│   └── test_amphipolis.py   # 4-cycle Amphipolis simulation
│
├── web/                     # Next.js 15 frontend (deploys to Vercel)
│   └── src/
│       ├── app/             # App Router pages + API routes
│       ├── components/      # React components (charts, panels, forms)
│       ├── hooks/           # useAuth, useAuditRealtime
│       └── lib/             # Supabase client, TypeScript types, Stripe
│
├── worker/                  # Python worker (deploys to Fly.io Machines)
│   ├── main.py              # Entry: read config → run engine → write to Supabase
│   ├── supabase_writer.py   # Real-time progress writer
│   ├── Dockerfile
│   └── fly.toml
│
├── supabase/                # Database layer
│   ├── migrations/          # 4 SQL migrations (profiles, audits, findings, billing)
│   └── functions/
│       └── trigger-worker/  # Edge Function: new audit → start Fly.io machine
│
└── .github/workflows/       # CI + deploy pipelines
```

## Key Commands

```bash
# Install and test the Python core
pip install -e ".[dev]"
pytest tests/ -v

# Run CLI in mock mode (no API calls)
epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology -v

# Run CLI in live mode (requires ANTHROPIC_API_KEY)
epistemix --topic "..." --country "..." --discipline "..." --live --budget 5.0

# Start web app locally
cd web && npm install && npm run dev

# Start local Supabase
docker-compose up supabase-db
```

## Dependency Graph (strict DAG — no circular imports)

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

**Rule:** Never import upward in this graph. `models.py` imports nothing from the project. `core.py` imports from everything above it. `run.py` only imports from `core.py`, `connector.py`, `models.py`, and `multi_agent.py`.

## Architecture Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| No external deps for core | stdlib only (dataclasses, enum, collections, re) | Portability, no version conflicts |
| `models.py` centralized | All data structures in one file | Prevents circular imports, clean DAG |
| MockConnector for tests | Pattern-matched canned responses | Zero API cost during development |
| Coverage as lower bound | Denominator grows as we discover more postulates | Philosophically honest — can never claim completeness |
| BFS for school detection | Connected components on undirected citation graph | No networkx dependency, O(V+E) |
| Evidence→discipline map | Keyword matching in `EVIDENCE_DISCIPLINE_MAP` | Extensible, no ML needed |
| Dual agents (α/β) | Different axiom weightings, not different prompts | Reproducible, deterministic with MockConnector |
| Scale-to-zero workers | Fly.io Machines with `auto_destroy: true` | $0 when no audits running |
| Supabase Realtime | Row-level changes on `audits` table | Frontend updates automatically, no polling |
| Weighted postulates (v3) | Confidence score per postulate (0.0–1.0) | Drives query strategy: VERIFY/STANDARD/RELIABLE/CONSOLIDATED |
| Negative postulates (v3) | Structured evidence of absence | Feedback loop: empty query → hypothesis → reformulated query |
| Temporal decay (v3) | Confidence decays per-domain rate | Archaeology 0.02/month, finance 0.15/month |

## The 7 Meta-Axioms

| ID | Name | What it predicts |
|----|------|-----------------|
| MA-01 | Linguistic Diversity | Research exists in multiple languages |
| MA-02 | Institutional Multiplicity | Multiple institutions are involved |
| MA-03 | Theoretical Pluralism | Competing theories exist |
| MA-04 | School Formation | Researchers cluster into citation schools |
| MA-05 | Disciplinary Breadth | Multiple disciplines contribute |
| MA-06 | Publication Channels | Multiple publication types exist |
| MA-07 | Temporal Evolution | Understanding has changed over time |

## Connector Abstraction

The `connector.py` module is the **only place** where AI provider coupling exists.

- **MockConnector**: Pattern-matched responses. Used in all 138 tests. Zero cost.
- **ClaudeConnector**: Anthropic SDK with `web_search_20250305` tool, budget tracking, retry with backoff.
- **Switching**: Set `ANTHROPIC_API_KEY` env var → worker uses `ClaudeConnector`. No key → falls back to `MockConnector`.

To add a new provider (OpenAI, Gemini, etc.): implement `BaseConnector` (3 methods: `query()`, `search()`, `total_cost`).

## Database Schema (Supabase PostgreSQL)

**Key tables:**
- `profiles` — User data, plan, BYOK key, monthly audit count. Auto-created via auth trigger.
- `audits` — One row per audit. Updated by worker in real-time. Realtime-enabled.
- `audit_findings` — Detailed findings (separate from JSONB on audits, for querying).
- `audit_anomalies` — Detailed anomalies.
- `usage_records` — Billing events.

**All tables have Row Level Security (RLS)**. Users can only see their own data. Workers use the service role key to bypass RLS.

## Billing Model

| Plan | Audits/month | Max cycles | Price |
|------|-------------|------------|-------|
| free | 3 | 2 | $0 |
| pro | unlimited | 10 | $29/mo |
| enterprise | unlimited | 10 | custom |

**BYOK (Bring Your Own Key)**: Users can provide their own Anthropic API key. Stored encrypted. Worker uses it directly.

## What NOT to Do

- Do NOT add dependencies to the Python core library (zero-dep policy for `src/epistemix/`)
- Do NOT import upward in the dependency graph
- Do NOT store secrets in code (use env vars)
- Do NOT add `networkx` — citation graph uses stdlib BFS
- Do NOT modify test fixtures in `conftest.py` without running all 138 tests
- Do NOT use `git push --force` on main
- Do NOT create always-on infrastructure (everything scales to zero)

## Current Status (v0.2.0)

**Done:**
- Complete Python core library (10 modules)
- Full test suite (138 tests, all passing)
- v3 Phase 1: WeightedPostulate with confidence scoring
- v3 Phase 2: NegativePostulate with empty-query feedback loop
- v3 Phase 7: Temporal decay (per-domain configurable)
- Next.js web app (landing, auth, dashboard, live audit page, 6 components)
- Fly.io worker (scale-to-zero, real-time progress)
- Supabase schema (4 migrations, RLS, Realtime, Edge Functions)
- CI/CD (GitHub Actions)
- Docker Compose for local dev
- Live validation: Antikythera mechanism test (Opus 4.6, Feb 2026)

**Not done yet — see TODO.md and PLAN.md:**
- v3 Phase 3: Semantic Relation Graph
- v3 Phase 4: Arabic + Chinese with access-barrier axioms
- v3 Phase 5: Cross-session memory (knowledge store)
- v3 Phase 6: Generative multi-agent
- v3 Phase 8: Auto-audit of axioms
- Stripe integration (billing checkout, webhook)
- PDF report generation
- Deployment to production (Vercel, Fly.io, Supabase Cloud)
