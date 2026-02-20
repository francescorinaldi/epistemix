"""Worker entry point — runs on Fly.io Machine (scale-to-zero).

Reads audit configuration from environment variables,
runs the epistemic engine, writes results back to Supabase,
then exits (machine auto-destroys).
"""

from __future__ import annotations

import os
import sys
import traceback

# Add the packages/core source to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from epistemix.connector import MockConnector, BaseConnector
from epistemix.core import EpistemicEngine
from epistemix.models import ResearchState
from epistemix.multi_agent import MultiAgentSystem
from supabase_writer import SupabaseWriter


def create_connector() -> BaseConnector:
    """Create the appropriate connector based on available credentials."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        from epistemix.connector import ClaudeConnector
        return ClaudeConnector(
            api_key=api_key,
            model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            max_budget=float(os.environ.get("MAX_BUDGET", "10.0")),
        )
    else:
        # Fallback to mock for development/testing
        print("WARNING: No ANTHROPIC_API_KEY — running in mock mode")
        return MockConnector()


def serialize_finding(f) -> dict:
    return {
        "name": f.name,
        "finding_type": f.finding_type.value,
        "description": f.description,
        "source_query": f.source_query,
        "language": f.language.value,
        "citations": f.citations,
        "metadata": f.metadata,
    }


def serialize_anomaly(a) -> dict:
    return {
        "id": a.id,
        "anomaly_type": a.anomaly_type.value,
        "severity": a.severity.value,
        "description": a.description,
        "suggested_queries": a.suggested_queries,
        "related_postulate_id": a.related_postulate_id,
        "detected_at_cycle": a.detected_at_cycle,
        "resolved": a.resolved,
    }


def serialize_postulate(p) -> dict:
    return {
        "id": p.id,
        "description": p.description,
        "meta_axiom_id": p.meta_axiom_id,
        "status": p.status.value,
        "confirming_findings": p.confirming_findings,
        "generated_at_cycle": p.generated_at_cycle,
    }


def main() -> None:
    audit_id = os.environ["AUDIT_ID"]
    topic = os.environ["AUDIT_TOPIC"]
    country = os.environ["AUDIT_COUNTRY"]
    discipline = os.environ["AUDIT_DISCIPLINE"]
    max_cycles = int(os.environ.get("AUDIT_MAX_CYCLES", "4"))

    writer = SupabaseWriter(audit_id)

    try:
        print(f"Starting audit: {topic} / {country} / {discipline}")
        print(f"Max cycles: {max_cycles}")

        connector = create_connector()

        # --- Phase 1: Single engine audit ---
        state = ResearchState(topic=topic, country=country, discipline=discipline)
        engine = EpistemicEngine(connector=connector, state=state, verbose=True)

        # Run cycles one by one for real-time progress updates
        for cycle in range(max_cycles):
            state.current_cycle = cycle
            coverage = engine.run_cycle(cycle)

            # Write progress after each cycle
            coverage_history = [
                {"cycle": c.cycle, "percentage": c.percentage, "confirmed": c.confirmed, "total": c.total}
                for c in state.coverage_history
            ]
            writer.update_cycle(
                cycle=cycle,
                coverage_history=coverage_history,
                findings_count=len(state.unique_findings),
                anomalies_count=len(state.anomalies),
            )
            writer.write_findings([serialize_finding(f) for f in state.findings])
            writer.write_postulates([serialize_postulate(p) for p in state.postulates])
            writer.write_anomalies([serialize_anomaly(a) for a in state.anomalies])

            print(f"Cycle {cycle}: coverage={coverage.percentage}%, findings={len(state.unique_findings)}, anomalies={len(state.anomalies)}")

            # Check convergence after cycle 2+
            if cycle >= 2 and len(state.coverage_history) >= 2:
                prev = state.coverage_history[-2].percentage
                curr = coverage.percentage
                if curr - prev < 2.0:
                    print(f"Convergence reached at cycle {cycle}")
                    break

            state.current_cycle += 1

        # --- Phase 2: Multi-agent analysis ---
        print("\nRunning multi-agent analysis...")
        mas = MultiAgentSystem(
            connector=connector,
            topic=topic,
            country=country,
            discipline=discipline,
            max_cycles=max_cycles,
        )
        multi_result = mas.run()
        writer.write_multi_agent_result(multi_result)

        # --- Phase 3: Write detailed records ---
        writer.write_detailed_findings(
            audit_id,
            [serialize_finding(f) for f in state.findings],
        )
        writer.write_detailed_anomalies(
            audit_id,
            [serialize_anomaly(a) for a in state.anomalies],
        )

        # --- Done ---
        writer.update_status("complete")
        print(f"\nAudit complete. Final coverage: {state.coverage_history[-1].percentage}%")

    except Exception as e:
        traceback.print_exc()
        writer.update_status("failed", error_message=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
