"""Supabase writer — writes audit progress back to the database in real-time.

Each update to the audits row triggers Supabase Realtime,
which pushes changes to the frontend via WebSocket.
"""

from __future__ import annotations

import json
import os
from typing import Any

from supabase import create_client, Client


class SupabaseWriter:
    """Writes audit progress and results to Supabase."""

    def __init__(self, audit_id: str) -> None:
        self.audit_id = audit_id
        self._client: Client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        )

    def update_status(self, status: str, error_message: str = "") -> None:
        """Update audit status."""
        data: dict[str, Any] = {"status": status}
        if error_message:
            data["error_message"] = error_message
        if status == "running":
            from datetime import datetime, timezone
            data["started_at"] = datetime.now(timezone.utc).isoformat()
        if status in ("complete", "failed"):
            from datetime import datetime, timezone
            data["completed_at"] = datetime.now(timezone.utc).isoformat()

        self._client.table("audits").update(data).eq("id", self.audit_id).execute()

    def update_cycle(
        self,
        cycle: int,
        coverage_history: list[dict],
    ) -> None:
        """Update current cycle progress — triggers Realtime push."""
        self._client.table("audits").update({
            "current_cycle": cycle,
            "coverage_history": coverage_history,
        }).eq("id", self.audit_id).execute()

    def write_findings(self, findings: list[dict]) -> None:
        """Write findings to the audits JSONB column."""
        self._client.table("audits").update({
            "findings": findings,
        }).eq("id", self.audit_id).execute()

    def write_anomalies(self, anomalies: list[dict]) -> None:
        """Write anomalies to the audits JSONB column."""
        self._client.table("audits").update({
            "anomalies": anomalies,
        }).eq("id", self.audit_id).execute()

    def write_postulates(self, postulates: list[dict]) -> None:
        """Write postulates to the audits JSONB column."""
        self._client.table("audits").update({
            "postulates": postulates,
        }).eq("id", self.audit_id).execute()

    def write_multi_agent_result(self, result: dict) -> None:
        """Write multi-agent analysis result."""
        self._client.table("audits").update({
            "multi_agent_result": result,
        }).eq("id", self.audit_id).execute()

    def write_detailed_findings(self, audit_id: str, findings: list[dict]) -> None:
        """Write individual findings to the audit_findings table."""
        rows = []
        for f in findings:
            rows.append({
                "audit_id": audit_id,
                "name": f["name"],
                "finding_type": f["finding_type"],
                "description": f.get("description", ""),
                "source_query": f.get("source_query", ""),
                "language": f.get("language", "en"),
                "citations": f.get("citations", []),
                "metadata": f.get("metadata", {}),
                "discovered_at_cycle": f.get("discovered_at_cycle", 0),
            })
        if rows:
            self._client.table("audit_findings").insert(rows).execute()

    def write_detailed_anomalies(self, audit_id: str, anomalies: list[dict]) -> None:
        """Write individual anomalies to the audit_anomalies table."""
        rows = []
        for a in anomalies:
            rows.append({
                "audit_id": audit_id,
                "anomaly_type": a["anomaly_type"],
                "severity": a["severity"],
                "description": a["description"],
                "suggested_queries": a.get("suggested_queries", []),
                "related_postulate_id": a.get("related_postulate_id", ""),
                "detected_at_cycle": a.get("detected_at_cycle", 0),
                "resolved": a.get("resolved", False),
            })
        if rows:
            self._client.table("audit_anomalies").insert(rows).execute()

    def record_usage(self, user_id: str, event_type: str, metadata: dict | None = None) -> None:
        """Record a usage event for billing."""
        self._client.table("usage_records").insert({
            "user_id": user_id,
            "audit_id": self.audit_id,
            "event_type": event_type,
            "metadata": metadata or {},
        }).execute()
