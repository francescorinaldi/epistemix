# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                │
│  Landing ─► Login ─► Dashboard ─► New Audit ─► Live Audit          │
│                                                   ▲                 │
│                                    Supabase Realtime (WebSocket)    │
└───────────────────────────────────────┬─────────────────────────────┘
                                        │ HTTPS
┌───────────────────────────────────────┼─────────────────────────────┐
│                        VERCEL (Next.js)                             │
│  ┌──────────┐  ┌────────────────┐  ┌─────────────┐                │
│  │ Pages    │  │ API Routes     │  │ Middleware   │                │
│  │ (React)  │  │ /api/v1/audits │  │ (Auth)      │                │
│  └──────────┘  └───────┬────────┘  └─────────────┘                │
└────────────────────────┼──────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────────┐
          ▼              ▼                  ▼
┌──────────────┐  ┌────────────┐   ┌─────────────┐
│  SUPABASE    │  │ FLY.IO     │   │  STRIPE     │
│              │  │ MACHINES   │   │  (future)   │
│ PostgreSQL   │  │            │   │ Per-audit   │
│ Auth         │  │ Python     │   │ billing     │
│ Realtime     │  │ workers    │   └─────────────┘
│ Edge Funcs   │  │            │
│ RLS          │  │ Scale to   │
│              │  │ ZERO       │
│  Trigger ────┼─►│ Start on   │
│  on INSERT   │  │ demand     │
│              │  │            │
│  Receives ◄──┼──┤ Write      │
│  updates     │  │ results    │
│              │  │            │
│  Realtime ───┼─►│ Stop when  │
│  to browser  │  │ done       │
└──────────────┘  └────────────┘
```

## Data Flow: Complete Audit Lifecycle

### 1. User Starts an Audit

```
Browser                Vercel                 Supabase
  │                      │                       │
  │  POST /api/v1/audits │                       │
  │─────────────────────►│                       │
  │                      │  auth.getUser()       │
  │                      │──────────────────────►│
  │                      │◄──────────────────────│
  │                      │                       │
  │                      │  check_audit_limit()  │
  │                      │──────────────────────►│
  │                      │◄──────────────────────│
  │                      │                       │
  │                      │  INSERT INTO audits   │
  │                      │──────────────────────►│
  │                      │                       │──── trigger: increment_audit_count()
  │                      │                       │──── trigger: notify_new_audit()
  │                      │                       │──── webhook: trigger-worker edge func
  │   { id: "abc-123" } │                       │
  │◄─────────────────────│                       │
  │                      │                       │
  │  redirect /audit/abc-123                     │
```

### 2. Edge Function Starts Worker

```
Supabase Edge Function              Fly.io Machines API
  │                                       │
  │  Read user profile (BYOK key?)        │
  │  Check plan limits                    │
  │  UPDATE audits SET status='running'   │
  │                                       │
  │  POST /v1/apps/epistemix-worker/machines
  │──────────────────────────────────────►│
  │                                       │──── Boot machine (~2s)
  │           { machine_id: "xyz" }       │──── Run worker/main.py
  │◄──────────────────────────────────────│
```

### 3. Worker Runs Audit Cycles

```
Fly.io Worker                    Supabase                    Anthropic API
  │                                 │                             │
  │  Read audit config from env     │                             │
  │                                 │                             │
  │  ┌─── CYCLE 0 ──────────────────────────────────────────┐    │
  │  │ initialize_postulates()                               │    │
  │  │ generate_initial_queries()  (multilingual)            │    │
  │  │ execute_queries() ──────────────────────────────────────►  │
  │  │                   ◄────────── search results ─────────────  │
  │  │ ingest_results()  → extract_entities()                │    │
  │  │ update_postulates()                                   │    │
  │  │ detect_anomalies()                                    │    │
  │  │ calculate_coverage()                                  │    │
  │  └───────────────────────────────────────────────────────┘    │
  │                                 │                             │
  │  UPDATE audits SET              │                             │
  │    current_cycle=0,             │                             │
  │    coverage_history=[...],      │                             │
  │    findings=[...],              │                             │
  │    anomalies=[...]              │                             │
  │────────────────────────────────►│                             │
  │                                 │──── Realtime push to browser│
  │                                 │                             │
  │  ┌─── CYCLE 1 ───────────────── (repeat) ───────────────┐    │
  │  │ generate_queries_from_anomalies()                     │    │
  │  │ execute → ingest → update → detect → coverage         │    │
  │  └───────────────────────────────────────────────────────┘    │
  │  ... cycles 2, 3 ... (until convergence or max)               │
  │                                 │                             │
  │  ┌─── MULTI-AGENT ──────────────────────────────────────┐    │
  │  │ Agent α runs full audit (institutional weights)       │    │
  │  │ Agent β runs full audit (theoretical weights)         │    │
  │  │ Arbiter compares → agreements, discrepancies,         │    │
  │  │                     known unknowns, blindness gap     │    │
  │  └───────────────────────────────────────────────────────┘    │
  │                                 │                             │
  │  UPDATE audits SET              │                             │
  │    status='complete',           │                             │
  │    multi_agent_result={...}     │                             │
  │────────────────────────────────►│                             │
  │                                 │──── Realtime push to browser│
  │                                 │                             │
  │  EXIT (machine auto-destroys)   │                             │
```

### 4. Browser Receives Real-Time Updates

```
Browser (React)               Supabase Realtime
  │                                │
  │  subscribe('audits', id=abc)   │
  │───────────────────────────────►│
  │                                │
  │  ... worker updates row ...    │
  │                                │
  │  { event: UPDATE, new: {...} } │
  │◄───────────────────────────────│
  │                                │
  │  setAudit(payload.new)         │
  │  → CoverageChart re-renders   │
  │  → AnomalyPanel re-renders    │
  │  → CycleTimeline updates      │
  │                                │
  │  ... more updates ...          │
  │                                │
  │  { status: 'complete' }        │
  │◄───────────────────────────────│
  │  → BlindnessGauge renders      │
```

---

## Python Core Library

### Module Responsibilities

| Module | Size | Responsibility |
|--------|------|---------------|
| `models.py` | 251 lines | **All data structures.** Finding, Postulate, Anomaly, Query, CoverageScore, ResearchState. Deduplication via `__hash__`/`__eq__`. Imports nothing from the project. |
| `meta_axioms.py` | 143 lines | **7 meta-axioms** with postulate templates. `generate_postulate_descriptions(topic, country, discipline)` returns `(axiom_id, description)` pairs. |
| `citation_graph.py` | 184 lines | **Directed adjacency list** (no networkx). BFS connected components for school detection. Citation islands = frequently cited but never searched. |
| `disciplines.py` | 165 lines | **Evidence→discipline mapping.** `EVIDENCE_DISCIPLINE_MAP`: inscriptions→epigraphy, bones→osteology, etc. Generates discipline postulates and detects gaps. |
| `content_analysis.py` | 243 lines | **Three analyzers + facade.** StructuralAbsence (found vs discussed), Convergence (echo chamber detection), EmptyQuery (patterns in failed searches). |
| `connector.py` | 271 lines | **AI provider abstraction.** `BaseConnector` ABC. `MockConnector` for tests (pattern-matched). `ClaudeConnector` for production (Anthropic SDK + web search tool). |
| `core.py` | 607 lines | **The brain.** `EpistemicEngine` orchestrates: initialize postulates → generate queries → execute → ingest → update → detect → coverage → repeat. Multilingual support. Entity extraction via regex. |
| `multi_agent.py` | 326 lines | **Dual-agent system.** Agent α (institutional weights), Agent β (theoretical weights). Each runs a full audit. `Arbiter` compares, finds agreements/discrepancies, promotes to known unknowns. |
| `run.py` | 195 lines | **CLI.** argparse-based. `--topic`, `--country`, `--discipline`, `--cycles`, `--live`/`--mock`, `--verbose`, `--output`, `--budget`, `--model`. |

### Dependency Graph

```
meta_axioms.py ──┐
                 │
models.py ───────┤  (imports nothing from project)
                 │
                 ├──► citation_graph.py   (imports: models)
                 ├──► disciplines.py      (imports: models)
                 ├──► content_analysis.py  (imports: models)
                 │
                 ├──► connector.py        (imports: nothing from project)
                 │       │
                 │       ▼
                 └──► core.py             (imports: ALL above)
                         │
                         ▼
                      multi_agent.py      (imports: core, connector, models, meta_axioms)
                         │
                         ▼
                      run.py              (imports: core, connector, models, multi_agent)
```

**Invariant:** No module imports from a module below it in this graph. This prevents circular imports and makes the codebase easy to reason about.

### Key Data Structures

```python
@dataclass
class Finding:
    name: str                    # "Katerina Peristeri"
    finding_type: FindingType    # SCHOLAR, THEORY, INSTITUTION, EVIDENCE, ...
    source_query: str            # Which query found this
    description: str
    language: QueryLanguage      # en, el, fr, de, ...
    citations: list[str]         # Names of cited entities
    # Dedup: __hash__ = (name.lower(), finding_type)

@dataclass
class Postulate:
    id: str                      # "P-MA01-00"
    description: str             # "Research exists in the local language"
    meta_axiom_id: str           # "MA-01"
    status: PostulateStatus      # UNCONFIRMED → CONFIRMED | REFUTED
    confirming_findings: list[str]

@dataclass
class Anomaly:
    id: str                      # "A-DISC-epigraphy"
    anomaly_type: AnomalyType    # LANGUAGE_GAP, DISCIPLINE_GAP, etc.
    severity: Severity           # CRITICAL, HIGH, MEDIUM
    description: str
    suggested_queries: list[str] # Queries to investigate this anomaly
    # Dedup: __hash__ = (anomaly_type, description.lower())

@dataclass
class CoverageScore:
    confirmed: int               # Postulates confirmed by findings
    total: int                   # Total postulates (grows over cycles!)
    anomaly_count: int
    cycle: int
    # percentage = confirmed/total (ALWAYS a lower bound)

@dataclass
class ResearchState:
    topic: str
    country: str
    discipline: str
    findings: list[Finding]
    postulates: list[Postulate]
    anomalies: list[Anomaly]
    queries: list[Query]
    coverage_history: list[CoverageScore]
    current_cycle: int
```

---

## Database Schema

### Entity Relationship

```
profiles (1) ──── (N) audits (1) ──── (N) audit_findings
    │                    │
    │                    └──── (N) audit_anomalies
    │
    └──── (N) usage_records
```

### Row Level Security

Every table has RLS enabled. Policies:

| Table | Policy | Effect |
|-------|--------|--------|
| `profiles` | `auth.uid() = id` | Users see only own profile |
| `audits` | `auth.uid() = user_id` | Users see only own audits |
| `audit_findings` | `EXISTS (audits WHERE user_id = auth.uid())` | Via audit ownership |
| `audit_anomalies` | `EXISTS (audits WHERE user_id = auth.uid())` | Via audit ownership |
| `usage_records` | `auth.uid() = user_id` | Users see own usage |

**Workers bypass RLS** using the Supabase service role key.

### Database Triggers

| Trigger | Table | When | Effect |
|---------|-------|------|--------|
| `on_auth_user_created` | `auth.users` | INSERT | Creates `profiles` row |
| `on_audit_created` | `audits` | INSERT | `pg_notify('new_audit', ...)` |
| `on_audit_increment_count` | `audits` | INSERT | Increments `profiles.audits_this_month` |
| `*_updated_at` | profiles, audits | UPDATE | Sets `updated_at = now()` |

### Supabase Realtime

The `audits` table is added to `supabase_realtime` publication. Any UPDATE to an audit row is pushed to subscribed clients via WebSocket. The frontend subscribes with:

```typescript
supabase.channel(`audit-${id}`)
  .on('postgres_changes', { event: 'UPDATE', table: 'audits', filter: `id=eq.${id}` },
    (payload) => setAudit(payload.new))
  .subscribe();
```

---

## Worker Architecture

### Lifecycle

1. **Created** by Supabase Edge Function via Fly.io Machines API
2. **Boots** in ~2 seconds (Python 3.11-slim Docker image)
3. **Reads** audit config from environment variables (`AUDIT_ID`, `AUDIT_TOPIC`, etc.)
4. **Runs** EpistemicEngine cycle by cycle, writing progress to Supabase after each
5. **Runs** MultiAgentSystem for dual-agent analysis
6. **Sets** `status='complete'` on the audit row
7. **Exits** → machine auto-destroys (`auto_destroy: true`)

### Connector Selection

```python
api_key = os.environ.get("ANTHROPIC_API_KEY")
if api_key:
    connector = ClaudeConnector(api_key=api_key)  # Live mode
else:
    connector = MockConnector()  # Development fallback
```

BYOK: If the user has set their own API key, the Edge Function passes it as `ANTHROPIC_API_KEY` to the worker.

### Cost Model

- **Machine**: shared-cpu-1x, 512MB RAM
- **Billing**: per second of compute (Fly.io)
- **Typical audit**: 2-5 minutes → ~$0.001-0.003 compute cost
- **When idle**: $0 (machines auto-destroy)

---

## Frontend Architecture

### Component Hierarchy

```
layout.tsx (global styles, dark theme)
├── page.tsx (landing)
├── auth/login/page.tsx (email + Google OAuth)
├── auth/callback/route.ts (OAuth redirect handler)
├── dashboard/page.tsx (audit history grid)
│   └── fetches audits from Supabase
├── audit/new/page.tsx
│   └── AuditForm.tsx (topic/country/discipline/cycles form)
└── audit/[id]/page.tsx (LIVE audit dashboard)
    ├── useAuditRealtime(id) → subscribes to Supabase Realtime
    ├── CycleTimeline (progress steps)
    ├── CoverageChart (Recharts line chart)
    ├── CitationGraph (D3 force-directed)
    ├── AnomalyPanel (severity-colored list)
    └── BlindnessGauge (multi-agent comparison)
```

### State Management

No Redux, no Zustand. State is minimal:

- **Auth state**: `useAuth()` hook → Supabase Auth
- **Audit state**: `useAuditRealtime(id)` hook → Supabase Realtime subscription
- **Form state**: `useState` in AuditForm component

The live audit page (`audit/[id]/page.tsx`) is essentially a read-only dashboard that re-renders when Supabase pushes updates.

---

## Security

| Concern | Mitigation |
|---------|-----------|
| Data isolation | Row Level Security on all tables |
| Auth | Supabase Auth (email + OAuth) |
| API key storage | Encrypted at app layer, never exposed to frontend |
| Worker access | Service role key (server-side only) |
| CORS | Handled by Vercel and Supabase defaults |
| Budget overflow | `ClaudeConnector` tracks cost, stops at budget |
| Plan limits | Enforced in DB (`check_audit_limit()` function) |
