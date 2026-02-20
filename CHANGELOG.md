# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2026-02-20

### Added

**Core Python Library**
- `models.py`: All data structures — Finding, Postulate, Anomaly, Query, CoverageScore, ResearchState with deduplication via `__hash__`/`__eq__`
- `meta_axioms.py`: 7 Level 0 meta-axioms (Linguistic Diversity, Institutional Multiplicity, Theoretical Pluralism, School Formation, Disciplinary Breadth, Publication Channels, Temporal Evolution) with postulate template generation
- `citation_graph.py`: Directed adjacency list with BFS connected components for school detection, citation islands, investigation priority ranking
- `disciplines.py`: Evidence-to-discipline mapping (`EVIDENCE_DISCIPLINE_MAP` with 35+ keyword→discipline entries), automatic postulate generation for expected disciplines, gap detection with severity rating
- `content_analysis.py`: Three analyzers (StructuralAbsence, Convergence, EmptyQuery) plus ContentAnalysisEngine facade
- `connector.py`: `BaseConnector` ABC, `MockConnector` with pattern-matched canned responses and call logging, `ClaudeConnector` with Anthropic SDK web search tool, budget tracking, and retry with exponential backoff, `extract_json()` utility
- `core.py`: `EpistemicEngine` — postulate initialization from meta-axioms, multilingual query generation (English, Greek, French, German, Italian, Turkish, Spanish), entity extraction via regex patterns, result ingestion and deduplication, postulate confirmation logic per axiom type, anomaly detection pipeline, coverage calculation as lower bound, cycle orchestration with convergence check
- `multi_agent.py`: `AgentPerspective` with axiom weightings, `EpistemicAgent` (runs full audit with weighted perspective), Agent α (institutional: MA-01/02/04/06) and Agent β (theoretical: MA-03/05/07), `Arbiter` (compares reports, finds agreements/discrepancies, promotes to known unknowns), `MultiAgentSystem` orchestrator
- `run.py`: CLI with argparse — `--topic`, `--country`, `--discipline`, `--cycles`, `--live`/`--mock`, `--verbose`, `--output`, `--budget`, `--model`, `--api-key`

**Test Suite**
- 113 tests across 9 test files, all passing
- `conftest.py`: Amphipolis domain fixtures and mock response data
- Integration tests: full pipeline single engine and multi-agent
- Amphipolis simulation: 4-cycle reference scenario

**Web Application (Next.js 15)**
- Landing page with feature highlights
- Authentication: email/password + Google OAuth via Supabase Auth
- Dashboard: audit history grid with status, coverage, findings, anomalies
- New audit form: topic, country, discipline, cycle slider with plan-based limits
- Live audit page: real-time updates via Supabase Realtime
- Components: CoverageChart (Recharts), AnomalyPanel (severity-colored), CitationGraph (D3 force-directed), CycleTimeline (step progress), BlindnessGauge (multi-agent comparison), AuditForm
- API routes: POST/GET `/api/v1/audits`, GET/POST `/api/v1/audits/:id`
- Hooks: `useAuth`, `useAuditRealtime`

**Worker (Fly.io)**
- Scale-to-zero Python worker with auto-destroy
- Reads config from env vars, runs EpistemicEngine + MultiAgentSystem
- Writes real-time progress to Supabase after each cycle
- Connector auto-detection: ClaudeConnector if API key present, MockConnector fallback
- Dockerfile: Python 3.11-slim with core library installed

**Database (Supabase PostgreSQL)**
- Migration 001: profiles table with auto-creation trigger, plan tracking
- Migration 002: audits table with status tracking, JSONB fields for results, Realtime publication, pg_notify trigger
- Migration 003: audit_findings and audit_anomalies detailed tables with RLS
- Migration 004: usage_records for billing, plan limit enforcement, monthly reset

**Infrastructure**
- Supabase Edge Function: `trigger-worker` — creates Fly.io Machine on new audit INSERT
- Docker Compose: local development with Supabase PostgreSQL
- GitHub Actions: CI (Python tests + TypeScript type check), deploy-web (Vercel), deploy-worker (Fly.io)
- `.gitignore` for Python, Node.js, environment files

**Documentation**
- `CLAUDE.md`: Project context for Claude Code instances
- `README.md`: Comprehensive project overview with architecture diagrams
- `ARCHITECTURE.md`: Deep technical architecture document
- `CONTRIBUTING.md`: Development guide for collaborators
- `TODO.md`: Roadmap with phases and priorities
- `CHANGELOG.md`: This file
- `DEPLOYMENT.md`: Step-by-step deployment guide
- `API.md`: REST API reference
- `PLAN.md`: Original implementation plan
