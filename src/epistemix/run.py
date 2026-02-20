"""CLI entry point for Epistemix epistemic audits.

Usage:
    epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology
    epistemix --topic "CRISPR gene editing" --country USA --discipline biology --cycles 5 --live

Orchestrates: engine → connector → cycle loop → auxiliary analyses → multi-agent → output.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from epistemix.core import EpistemixEngine
from epistemix.citation_graph import CitationGraph
from epistemix.content_analysis import ContentAnalysisEngine
from epistemix.disciplines import DisciplineAnalyzer
from epistemix.multi_agent import MultiAgentSystem
from epistemix.connector import BaseConnector, ClaudeConnector, MockConnector
from epistemix.models import Finding


def create_connector(args: argparse.Namespace) -> BaseConnector:
    """Create the appropriate connector based on CLI args."""
    if args.live:
        api_key = args.api_key or None
        return ClaudeConnector(
            api_key=api_key,
            model=args.model,
            max_budget=args.budget,
        )
    return MockConnector()


def run_audit(
    topic: str,
    country: str,
    discipline: str,
    connector: BaseConnector,
    max_cycles: int = 4,
    queries_per_cycle: int = 10,
    convergence_threshold: float = 2.0,
    verbose: bool = False,
) -> dict[str, Any]:
    """Run a complete epistemic audit.

    Returns the full result as a serializable dict.
    """
    engine = EpistemixEngine(country, topic, discipline)

    # Initialize queries
    queries = engine.initialize()
    if verbose:
        print(f"Generated {len(queries)} initial queries")

    # Cycle loop
    prev_coverage = -1.0
    for cycle_num in range(max_cycles):
        # Execute queries via connector
        findings = connector.execute_batch(queries, limit=queries_per_cycle)

        if verbose:
            print(f"\nCycle {cycle_num + 1}: {len(findings)} findings from "
                  f"{len(queries)} queries")

        # Ingest findings
        new_entities = engine.ingest_findings(findings)
        if verbose and new_entities:
            print(f"  New entities: {', '.join(new_entities[:10])}")

        # Run cycle
        snapshot = engine.run_cycle()

        if verbose:
            print(f"  Coverage: {snapshot.coverage_score:.1f}%")
            print(f"  Expectations: {snapshot.n_expectations_met}/"
                  f"{snapshot.n_expectations}")
            print(f"  Anomalies: {snapshot.n_anomalies}")

        # Convergence check
        if (
            abs(snapshot.coverage_score - prev_coverage) < convergence_threshold
            and cycle_num > 0
        ):
            if verbose:
                print(f"  Converged (delta < {convergence_threshold})")
            break
        prev_coverage = snapshot.coverage_score

        # Next cycle queries
        queries = engine.pending_queries

    # Auxiliary analyses
    citation_graph = CitationGraph()
    citation_graph.build_from_findings(engine.findings)
    cg_anomalies = citation_graph.generate_anomalies()

    discipline_analyzer = DisciplineAnalyzer(discipline)
    discipline_analyzer.ingest_findings(engine.findings)
    disc_anomalies = discipline_analyzer.generate_anomalies()

    content_engine = ContentAnalysisEngine()
    content_anomalies = content_engine.generate_all_anomalies()

    # Multi-agent
    multi_agent = MultiAgentSystem(engine.postulates)
    multi_agent_result = multi_agent.run(engine.findings)

    # Compile result
    result = engine.to_dict()
    result["citation_graph"] = citation_graph.summary()
    result["citation_anomalies"] = [a.to_dict() for a in cg_anomalies]
    result["discipline_coverage"] = discipline_analyzer.coverage_summary()
    result["discipline_anomalies"] = [a.to_dict() for a in disc_anomalies]
    result["content_anomalies"] = [a.to_dict() for a in content_anomalies]
    result["multi_agent_result"] = multi_agent_result
    result["total_cost"] = connector.total_cost
    result["total_api_calls"] = connector.call_count

    return result


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Epistemix — Epistemic Audit Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--topic", required=True, help="Research topic")
    parser.add_argument("--country", required=True, help="Country context")
    parser.add_argument(
        "--discipline", default="archaeology", help="Academic discipline"
    )
    parser.add_argument(
        "--cycles", type=int, default=4, help="Max audit cycles (1-10)"
    )
    parser.add_argument(
        "--queries-per-cycle", type=int, default=10,
        help="Max queries per cycle",
    )
    parser.add_argument(
        "--convergence", type=float, default=2.0,
        help="Convergence threshold (stop if delta < threshold)",
    )
    parser.add_argument(
        "--live", action="store_true",
        help="Use Claude API (requires API key)",
    )
    parser.add_argument(
        "--mock", action="store_true", help="Use mock connector (default)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show queries without executing",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--output", "-o", type=str, help="Output file (JSON)",
    )
    parser.add_argument(
        "--budget", type=float, default=10.0,
        help="Max API budget in dollars",
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-20250514",
        help="Claude model to use",
    )
    parser.add_argument("--api-key", help="Anthropic API key")

    args = parser.parse_args()

    # Dry run mode
    if args.dry_run:
        engine = EpistemixEngine(args.country, args.topic, args.discipline)
        queries = engine.initialize()
        print(f"Would execute {len(queries)} initial queries:\n")
        for q in queries:
            print(f"  [{q.language}] {q.query}")
            print(f"    Rationale: {q.rationale}")
            print(f"    Priority: {q.priority.value}")
        return

    connector = create_connector(args)

    result = run_audit(
        topic=args.topic,
        country=args.country,
        discipline=args.discipline,
        connector=connector,
        max_cycles=args.cycles,
        queries_per_cycle=args.queries_per_cycle,
        convergence_threshold=args.convergence,
        verbose=args.verbose,
    )

    # Output
    output = json.dumps(result, indent=2, default=str)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        if args.verbose:
            print(f"\nResults written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
