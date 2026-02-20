# API Reference

## Authentication

All API endpoints require authentication via Supabase Auth. The frontend handles this automatically via cookies. For programmatic access (enterprise), use an API key in the `Authorization` header.

### Cookie-based (web app)

Authentication is handled automatically when using the web interface. Supabase sets auth cookies on login.

### Token-based (future — enterprise API)

```
Authorization: Bearer <api-key>
```

---

## Endpoints

### Create Audit

**`POST /api/v1/audits`**

Start a new epistemic audit. Creates an audit row in the database, which triggers the worker to begin processing.

**Request body:**

```json
{
  "topic": "Amphipolis tomb excavation",
  "country": "Greece",
  "discipline": "archaeology",
  "max_cycles": 4
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | Yes | Research topic to audit |
| `country` | string | Yes | Country context (determines languages) |
| `discipline` | string | Yes | Academic discipline |
| `max_cycles` | integer | No | Max audit cycles, 1-10 (default: 4, capped by plan) |

**Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errors:**

| Status | Body | Cause |
|--------|------|-------|
| 400 | `{"error": "topic, country, and discipline are required"}` | Missing required field |
| 401 | `{"error": "Unauthorized"}` | Not authenticated |
| 404 | `{"error": "Profile not found"}` | User has no profile (should not happen) |
| 429 | (via Edge Function) | Monthly audit limit reached |
| 500 | `{"error": "Failed to create audit"}` | Database error |

---

### List Audits

**`GET /api/v1/audits`**

Returns all audits for the authenticated user, sorted by creation date (newest first).

**Response (200 OK):**

```json
{
  "audits": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "topic": "Amphipolis tomb excavation",
      "country": "Greece",
      "discipline": "archaeology",
      "status": "complete",
      "current_cycle": 3,
      "coverage_history": [
        {"cycle": 0, "percentage": 38.5},
        {"cycle": 1, "percentage": 57.1},
        {"cycle": 2, "percentage": 69.2},
        {"cycle": 3, "percentage": 75.0}
      ],
      "created_at": "2026-02-20T14:30:00Z"
    }
  ]
}
```

---

### Get Audit

**`GET /api/v1/audits/:id`**

Returns full audit details including findings, anomalies, postulates, and multi-agent results.

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "...",
  "topic": "Amphipolis tomb excavation",
  "country": "Greece",
  "discipline": "archaeology",
  "max_cycles": 4,
  "status": "complete",
  "current_cycle": 3,
  "error_message": null,
  "coverage_history": [
    {"cycle": 0, "percentage": 38.5, "confirmed": 5, "total": 13},
    {"cycle": 1, "percentage": 57.1, "confirmed": 8, "total": 14},
    {"cycle": 2, "percentage": 69.2, "confirmed": 9, "total": 13},
    {"cycle": 3, "percentage": 75.0, "confirmed": 12, "total": 16}
  ],
  "findings": [
    {
      "name": "Katerina Peristeri",
      "finding_type": "scholar",
      "description": "Lead excavator of the Amphipolis tomb",
      "source_query": "Amphipolis tomb key researchers",
      "language": "en",
      "citations": ["Lazaridis", "Lefantzis"],
      "metadata": {}
    }
  ],
  "postulates": [
    {
      "id": "P-MA01-00",
      "description": "Research on Amphipolis tomb excavation in Greece exists in the local language(s)",
      "meta_axiom_id": "MA-01",
      "status": "confirmed",
      "confirming_findings": ["Greek publication in Archaiologiko Deltion"],
      "generated_at_cycle": 0
    }
  ],
  "anomalies": [
    {
      "id": "A-DISC-epigraphy",
      "anomaly_type": "discipline_gap",
      "severity": "critical",
      "description": "No epigraphy specialist found despite evidence of inscriptions",
      "suggested_queries": ["epigraphy specialist research", "epigraphy analysis findings"],
      "related_postulate_id": "P-DISC-001",
      "detected_at_cycle": 1,
      "resolved": false
    }
  ],
  "multi_agent_result": {
    "alpha": {
      "coverage": 71.0,
      "findings": 14,
      "anomalies": 0,
      "coverage_history": [
        {"cycle": 0, "percentage": 40.0},
        {"cycle": 1, "percentage": 71.0}
      ]
    },
    "beta": {
      "coverage": 67.0,
      "findings": 12,
      "anomalies": 5,
      "coverage_history": [
        {"cycle": 0, "percentage": 35.0},
        {"cycle": 1, "percentage": 67.0}
      ]
    },
    "combined": {
      "coverage": 54.0,
      "blindness_gap": 17.0,
      "total_anomalies": 5,
      "known_unknowns": 3
    },
    "agreements": [
      "8 findings agreed upon by both agents"
    ],
    "discrepancies": [
      "Agent α found 6 entities not found by β",
      "Agent β detected discipline_gap but α missed it"
    ],
    "known_unknowns": [
      {
        "type": "discipline_gap",
        "severity": "high",
        "description": "[Known Unknown] Agent β detected but α missed: No epigraphy specialist found"
      }
    ]
  },
  "report_url": null,
  "started_at": "2026-02-20T14:30:05Z",
  "completed_at": "2026-02-20T14:33:22Z",
  "created_at": "2026-02-20T14:30:00Z",
  "updated_at": "2026-02-20T14:33:22Z"
}
```

**Errors:**

| Status | Body | Cause |
|--------|------|-------|
| 401 | `{"error": "Unauthorized"}` | Not authenticated |
| 404 | `{"error": "Audit not found"}` | Invalid ID or belongs to another user |

---

### Stop Audit

**`POST /api/v1/audits/:id`**

Stop a running audit early.

**Request body:**

```json
{
  "action": "stop"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Audit stopped"
}
```

**Note:** This sets the audit status to `complete`. The worker may still be running for a few seconds until it checks the status.

---

## Realtime Subscription

For live audit progress, subscribe to Supabase Realtime changes on the `audits` table:

```typescript
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const channel = supabase
  .channel("audit-live")
  .on(
    "postgres_changes",
    {
      event: "UPDATE",
      schema: "public",
      table: "audits",
      filter: `id=eq.${auditId}`,
    },
    (payload) => {
      console.log("Audit updated:", payload.new);
      // payload.new contains the full updated audit row
    }
  )
  .subscribe();
```

Updates are pushed after each cycle completes (~every 30-60 seconds with live API).

---

## Data Types

### Audit Status

| Value | Meaning |
|-------|---------|
| `pending` | Created, worker not yet started |
| `running` | Worker is processing cycles |
| `complete` | All cycles finished (or stopped early) |
| `failed` | Worker encountered an error |

### Finding Type

| Value | Description |
|-------|-------------|
| `scholar` | Researcher, academic |
| `theory` | Theoretical framework, hypothesis |
| `institution` | University, museum, government body |
| `publication` | Journal, book, conference proceedings |
| `school` | Research group, citation cluster |
| `evidence` | Artifact, specimen, data |
| `method` | Research methodology |
| `event` | Historical event, discovery |
| `other` | Uncategorized |

### Anomaly Type

| Value | Description |
|-------|-------------|
| `language_gap` | Expected language not found in sources |
| `theory_gap` | Too few competing theories |
| `discipline_gap` | Evidence type found but no specialist |
| `institution_gap` | Expected institutions not found |
| `school_gap` | Only one citation school detected |
| `publication_gap` | Missing publication channels |
| `temporal_gap` | Research doesn't span expected time range |
| `citation_island` | Scholar cited often but never searched |
| `convergence_excess` | Sources agree too much (echo chamber) |
| `divergence_excess` | No agreement between sources |
| `structural_absence` | Entities found but not discussed |
| `empty_query_pattern` | Systematic pattern in failed queries |

### Severity

| Value | Meaning |
|-------|---------|
| `critical` | Fundamental blind spot — immediate investigation needed |
| `high` | Significant gap — likely to affect conclusions |
| `medium` | Notable absence — worth investigating |
