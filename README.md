# Epistemix

### Map the boundaries of what is known — and what isn't.

Epistemix is an epistemic audit framework. Given any research topic, it predicts what knowledge *should* exist — then searches for it. The gap between expectation and reality reveals the blind spots that no one is looking for: missing languages, absent disciplines, overlooked scholars, unexamined theories.

Coverage is always reported as a **lower bound**. The denominator grows as we discover more postulates. We can never claim completeness — only measure how much of the map we've drawn so far.

---

## Why This Matters

Systematic reviews find what's *there*. They cannot detect what's *missing*.

If an entire language tradition of scholarship exists but nobody on the review team reads that language, the gap is invisible. If a field has been studied by archaeologists but not geophysicists, and no one thinks to ask, the absence goes unnoticed. If three research schools cite each other but never engage a fourth, that fourth school is a blind spot — and the other three will never tell you about it.

These aren't edge cases. They are the *default state* of knowledge. Every field, every topic, every country has them.

Epistemix makes these gaps visible.

**Reference scenarios:**
- **[Amphipolis tomb excavation](https://en.wikipedia.org/wiki/Amphipolis)** (Greece, archaeology) — Rich multilingual scholarship, competing archaeological theories, documented citation islands between Greek and international research communities. All test fixtures and mock data use this scenario.
- **[Antikythera mechanism](https://en.wikipedia.org/wiki/Antikythera_mechanism)** (Greece, archaeology/history of science) — Live validation scenario, tested Feb 2026 with 7 languages, 4 cycles, 50+ sources, 30+ scholars.

---

## How It Works

Epistemix runs in iterative cycles. Each cycle generates hypotheses about what should exist, searches for it, extracts what it finds, and flags what's missing. Over multiple cycles, coverage converges.

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
┌─────────────────┐     Coverage = confirmed / total postulates
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

These are domain-independent structural properties of academic research. If a topic is sufficiently studied, all seven should hold. When one doesn't, that's a signal.

| ID | Axiom | What it predicts |
|----|-------|-----------------|
| MA-01 | Linguistic Diversity | Research exists in multiple languages |
| MA-02 | Institutional Multiplicity | Multiple institutions are involved |
| MA-03 | Theoretical Pluralism | Competing theories exist |
| MA-04 | School Formation | Researchers cluster into citation schools |
| MA-05 | Disciplinary Breadth | Multiple disciplines contribute |
| MA-06 | Publication Channels | Multiple publication types exist (journals, conferences, grey lit) |
| MA-07 | Temporal Evolution | Understanding has changed over decades |

### Dual-Agent Audit

To guard against the system's own biases, Epistemix runs two independent agents with different axiom weightings, then compares their results.

| Agent | Focus | High-weight axioms |
|-------|-------|--------------------|
| Agent α (institutional) | Languages, institutions, schools, publications | MA-01, MA-02, MA-04, MA-06 |
| Agent β (theoretical) | Theories, disciplines, temporal evolution | MA-03, MA-05, MA-07 |
| Arbiter | Compares reports, promotes disagreements to **known unknowns** | — |

**Combined coverage** = min(α, β). The **blindness gap** = max(α, β) - min(α, β). Where the two agents disagree is where the real blind spots live.

---

## See It In Action

```bash
# Install (zero dependencies for the core library)
pip install -e ".[dev]"

# Run an audit in mock mode — no API calls, instant results
epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology -v
```

Output: postulates generated, multilingual queries executed, entities extracted, anomalies flagged, coverage calculated — all in under a second.

---

## Quick Start

### Install

```bash
pip install -e ".[dev]"     # development (mock mode, zero API cost)
pip install -e ".[live]"    # production (adds anthropic SDK)
```

### CLI

```bash
# Mock mode — pattern-matched responses, no API calls
epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology -v

# Live mode — real Claude API calls with web search
export ANTHROPIC_API_KEY="sk-ant-..."
epistemix --topic "CRISPR gene editing" --country USA --discipline biology --live --budget 5.0 -v

# Export to JSON
epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology -o report.json
```

### Python API

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

### Tests

```bash
pytest tests/ -v              # all 138 tests
pytest tests/test_core.py -v  # just core engine tests
pytest tests/ -v --tb=short   # short traceback on failure
```

---

## Web Application

The web app provides a full interface for running audits with real-time progress updates.

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

See [docs/API.md](docs/API.md) for the full reference.

---

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the complete technical architecture.

### Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Next.js 15 on Vercel | Free tier, edge network, zero-config deploys |
| Database + Auth | Supabase (PostgreSQL) | RLS, Realtime, Auth, Edge Functions — one service |
| Workers | Fly.io Machines | **Scale to zero** — $0 when idle, pay per second |
| Core engine | Python 3.10+ (zero deps) | Portable, testable, no vendor lock-in |
| AI provider | Anthropic Claude API | Via `connector.py` abstraction (swappable) |
| CI/CD | GitHub Actions | Native, free |

### Cost at Scale

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
├── src/epistemix/           # Core Python library (zero external dependencies)
│   ├── models.py            # Data structures (Finding, Postulate, Anomaly, Query, etc.)
│   ├── meta_axioms.py       # 7 Level 0 meta-axioms
│   ├── citation_graph.py    # BFS school detection, citation islands
│   ├── disciplines.py       # Evidence → discipline mapping
│   ├── content_analysis.py  # Structural absence, convergence, empty queries
│   ├── connector.py         # MockConnector / ClaudeConnector (swappable)
│   ├── core.py              # EpistemicEngine — the main audit orchestrator
│   ├── multi_agent.py       # Agent α, Agent β, Arbiter
│   └── run.py               # CLI entry point
├── tests/                   # 138 tests (pytest, zero API cost)
├── web/                     # Next.js 15 frontend (Vercel)
├── worker/                  # Python audit worker (Fly.io, scale-to-zero)
├── supabase/                # DB migrations + Edge Functions
├── docs/                    # Architecture, API, deployment, contributing
├── .github/workflows/       # CI/CD pipelines
└── docker-compose.yml       # Local development
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | Project context for Claude Code instances |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture and design decisions |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | How to develop, test, and contribute |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Step-by-step deployment guide |
| [docs/API.md](docs/API.md) | REST API reference |
| [docs/PLAN.md](docs/PLAN.md) | Project plan and roadmap |

---

## License

MIT
