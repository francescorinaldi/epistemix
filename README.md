# Epistemix

**Epistemic audit framework — detect unknown unknowns in research.**

Epistemix predicts what knowledge *should* exist about a topic, then verifies whether it does. The gap between expectation and reality reveals blind spots: missing languages, absent disciplines, overlooked scholars, and unexamined theories.

> "The most dangerous gaps in knowledge are the ones you don't know exist."

---

## How It Works

```
Topic + Country + Discipline
        │
        ▼
┌─────────────────┐     7 meta-axioms predict what
│  POSTULATE       │◄─── knowledge should exist
│  GENERATION      │     (languages, theories, institutions...)
└────────┬────────┘
         ▼
┌─────────────────┐     Multilingual queries in English,
│  QUERY           │◄─── Greek, French, German, Italian, etc.
│  GENERATION      │
└────────┬────────┘
         ▼
┌─────────────────┐     Extract scholars, institutions,
│  ENTITY          │◄─── theories, evidence from responses
│  EXTRACTION      │
└────────┬────────┘
         ▼
┌─────────────────┐     Compare findings against postulates.
│  ANOMALY         │◄─── Flag gaps: missing disciplines,
│  DETECTION       │     citation islands, echo chambers
└────────┬────────┘
         ▼
┌─────────────────┐     Coverage = confirmed/total postulates
│  COVERAGE        │◄─── (always a LOWER BOUND — denominator
│  CALCULATION     │      grows as we discover more)
└────────┬────────┘
         ▼
  Repeat for N cycles (coverage converges)
         │
         ▼
┌─────────────────┐     Two agents with different biases
│  MULTI-AGENT     │◄─── independently audit. Where they
│  ANALYSIS        │     DISAGREE = proven blind spots.
└─────────────────┘
```

### The 7 Meta-Axioms

These are domain-independent truths about how academic research works:

| ID | Axiom | What it predicts |
|----|-------|-----------------|
| MA-01 | Linguistic Diversity | Research exists in multiple languages |
| MA-02 | Institutional Multiplicity | Multiple institutions are involved |
| MA-03 | Theoretical Pluralism | Competing theories exist |
| MA-04 | School Formation | Researchers cluster into citation schools |
| MA-05 | Disciplinary Breadth | Multiple disciplines contribute |
| MA-06 | Publication Channels | Multiple publication types exist (journals, conferences, grey lit) |
| MA-07 | Temporal Evolution | Understanding has changed over decades |

### Dual-Agent System

| Agent | Focus | High-weight axioms |
|-------|-------|--------------------|
| Agent α (institutional) | Languages, institutions, schools, publications | MA-01, MA-02, MA-04, MA-06 |
| Agent β (theoretical) | Theories, disciplines, temporal evolution | MA-03, MA-05, MA-07 |
| Arbiter | Compares reports, promotes disagreements to **known unknowns** | — |

**Combined coverage** = min(α, β). The **blindness gap** = max(α,β) - min(α,β).

---

## Quick Start

### Install

```bash
pip install -e ".[dev]"     # development (mock mode, zero API cost)
pip install -e ".[live]"    # production (adds anthropic SDK)
```

### Run (CLI)

```bash
# Mock mode — no API calls, instant results
epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology -v

# Live mode — real Claude API calls
export ANTHROPIC_API_KEY="sk-ant-..."
epistemix --topic "CRISPR gene editing" --country USA --discipline biology --live --budget 5.0 -v

# Output to JSON file
epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology -o report.json
```

### Run (Python API)

```python
from epistemix.connector import MockConnector
from epistemix.core import EpistemicEngine
from epistemix.models import ResearchState
from epistemix.multi_agent import MultiAgentSystem

# Single engine audit
connector = MockConnector()
state = ResearchState(
    topic="Amphipolis tomb excavation",
    country="Greece",
    discipline="archaeology",
)
engine = EpistemicEngine(connector=connector, state=state, verbose=True)
coverage_history = engine.run_all_cycles(max_cycles=4)

print(f"Final coverage: {coverage_history[-1].percentage}%")
print(f"Findings: {len(state.unique_findings)}")
print(f"Anomalies: {len(state.anomalies)}")

# Multi-agent audit
mas = MultiAgentSystem(
    connector=connector,
    topic="Amphipolis tomb excavation",
    country="Greece",
    discipline="archaeology",
)
result = mas.run()
print(f"Alpha coverage: {result['alpha']['coverage']}%")
print(f"Beta coverage:  {result['beta']['coverage']}%")
print(f"Blindness gap:  {result['combined']['blindness_gap']} points")
print(f"Known unknowns: {result['combined']['known_unknowns']}")
```

### Test

```bash
pytest tests/ -v              # all 113 tests
pytest tests/test_core.py -v  # just core engine tests
pytest tests/ -v --tb=short   # short traceback on failure
```

---

## Web Application

The web app provides a complete UI for running audits with real-time progress.

### Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/auth/login` | Email/password + Google OAuth |
| `/dashboard` | User's audit history (grid view) |
| `/audit/new` | New audit form (topic, country, discipline, cycles) |
| `/audit/:id` | **Live audit dashboard** — real-time updates via Supabase Realtime |

### Components

| Component | What it shows |
|-----------|---------------|
| `CoverageChart` | Recharts line chart — coverage % over cycles |
| `AnomalyPanel` | Severity-colored anomaly list (critical/high/medium) |
| `CitationGraph` | D3 force-directed graph of scholars and citations |
| `CycleTimeline` | Step-by-step progress indicator with pulse animation |
| `BlindnessGauge` | Multi-agent comparison (α vs β vs combined) |
| `AuditForm` | Topic/country/discipline form with plan-based limits |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/audits` | Start a new audit |
| `GET` | `/api/v1/audits` | List user's audits |
| `GET` | `/api/v1/audits/:id` | Get audit status + results |
| `POST` | `/api/v1/audits/:id` | Stop an audit (`{action: "stop"}`) |

See [API.md](API.md) for full reference.

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the complete technical architecture.

### Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 15 on Vercel | Free tier, edge network, zero-config deploys |
| Database + Auth | Supabase (PostgreSQL) | RLS, Realtime, Auth, Edge Functions — one service |
| Workers | Fly.io Machines | **Scale to zero** — $0 when idle, pay per second |
| Core engine | Python 3.10+ (zero deps) | Portable, testable, no vendor lock-in |
| AI provider | Anthropic Claude API | Via `connector.py` abstraction (swappable) |
| CI/CD | GitHub Actions | Native, free |

### Cost

| Scale | Monthly cost |
|-------|-------------|
| 0 users | $0 (all free tiers) |
| 100 users, ~500 audits | ~$25 (Supabase Pro) |
| 1K users, ~5K audits | ~$50-75 (Supabase + Fly.io) |
| Claude API | BYOK (user pays) or metered via Stripe |

---

## Project Structure

```
epistemix/
├── src/epistemix/           # Core Python library
│   ├── models.py            # Data structures (Finding, Postulate, Anomaly, Query, etc.)
│   ├── meta_axioms.py       # 7 Level 0 meta-axioms
│   ├── citation_graph.py    # BFS school detection, citation islands
│   ├── disciplines.py       # Evidence → discipline mapping
│   ├── content_analysis.py  # Structural absence, convergence, empty queries
│   ├── connector.py         # MockConnector / ClaudeConnector
│   ├── core.py              # EpistemicEngine (607 lines — the brain)
│   ├── multi_agent.py       # Agent α, Agent β, Arbiter
│   └── run.py               # CLI
├── tests/                   # 113 tests
├── web/                     # Next.js frontend
├── worker/                  # Fly.io worker
├── supabase/                # DB migrations + Edge Functions
├── .github/workflows/       # CI/CD
└── docker-compose.yml       # Local dev
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | Project context for Claude Code instances |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical architecture and design decisions |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to develop, test, and contribute |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Step-by-step deployment guide |
| [API.md](API.md) | REST API reference |
| [TODO.md](TODO.md) | Current status and roadmap |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

---

## License

MIT
