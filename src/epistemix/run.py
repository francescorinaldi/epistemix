"""CLI entry point for Epistemix epistemic audits.

Usage:
    epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology
    epistemix --topic "CRISPR gene editing" --country USA --discipline biology --cycles 5 --live
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from epistemix.connector import BaseConnector, MockConnector
from epistemix.core import EpistemicEngine
from epistemix.models import ResearchState, Severity
from epistemix.multi_agent import MultiAgentSystem


def create_connector(args: argparse.Namespace) -> BaseConnector:
    """Create the appropriate connector based on CLI args."""
    if args.live:
        try:
            from epistemix.connector import ClaudeConnector
            return ClaudeConnector(
                api_key=args.api_key,
                model=args.model,
                max_budget=args.budget,
            )
        except ImportError:
            print(
                "Error: --live requires the 'anthropic' package. "
                "Install with: pip install 'epistemix[live]'",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        return MockConnector()


def format_anomaly(anomaly: Any) -> str:
    """Format an anomaly for display."""
    severity_markers = {
        Severity.CRITICAL: "!!",
        Severity.HIGH: "! ",
        Severity.MEDIUM: "  ",
    }
    marker = severity_markers.get(anomaly.severity, "  ")
    return f"  [{marker}] [{anomaly.severity.value:>8}] {anomaly.description}"


def run_audit(args: argparse.Namespace) -> dict:
    """Run the epistemic audit and return results."""
    connector = create_connector(args)

    if args.verbose:
        print(f"Topic:      {args.topic}")
        print(f"Country:    {args.country}")
        print(f"Discipline: {args.discipline}")
        print(f"Cycles:     {args.cycles}")
        print(f"Mode:       {'LIVE' if args.live else 'MOCK'}")
        print("=" * 60)

    # Run single engine
    state = ResearchState(
        topic=args.topic,
        country=args.country,
        discipline=args.discipline,
    )
    engine = EpistemicEngine(
        connector=connector,
        state=state,
        verbose=args.verbose,
    )
    coverage_history = engine.run_all_cycles(max_cycles=args.cycles)

    # Print progress
    if args.verbose:
        print("\n" + "=" * 60)
        print("SINGLE ENGINE RESULTS")
        print("=" * 60)
        print(f"Findings: {len(state.unique_findings)}")
        print(f"Final coverage: {coverage_history[-1].percentage}%")
        print(f"Anomalies: {len(state.anomalies)}")
        if state.anomalies:
            print("\nAnomalies detected:")
            for a in sorted(state.anomalies, key=lambda x: x.severity):
                print(format_anomaly(a))

    # Run multi-agent system
    if args.verbose:
        print("\n" + "=" * 60)
        print("MULTI-AGENT ANALYSIS")
        print("=" * 60)

    mas = MultiAgentSystem(
        connector=connector,
        topic=args.topic,
        country=args.country,
        discipline=args.discipline,
        max_cycles=args.cycles,
    )
    multi_result = mas.run()

    if args.verbose:
        print(f"Agent α coverage: {multi_result['alpha']['coverage']}%")
        print(f"Agent β coverage: {multi_result['beta']['coverage']}%")
        print(f"Combined coverage: {multi_result['combined']['coverage']}%")
        print(f"Blindness gap: {multi_result['combined']['blindness_gap']} points")
        print(f"Known unknowns: {multi_result['combined']['known_unknowns']}")

        if multi_result["discrepancies"]:
            print("\nDiscrepancies:")
            for d in multi_result["discrepancies"]:
                print(f"  - {d}")

        if multi_result["known_unknowns"]:
            print("\nKnown unknowns:")
            for ku in multi_result["known_unknowns"]:
                print(f"  [{ku['severity']:>8}] {ku['description']}")

    # Build final result
    result = {
        "single_engine": state.to_dict(),
        "multi_agent": multi_result,
    }

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="epistemix",
        description="Epistemix — Epistemic Audit Framework. Detect unknown unknowns in research.",
    )
    parser.add_argument(
        "--topic", required=True, help="Research topic to audit"
    )
    parser.add_argument(
        "--country", required=True, help="Country context"
    )
    parser.add_argument(
        "--discipline", required=True, help="Academic discipline"
    )
    parser.add_argument(
        "--cycles", type=int, default=4, help="Max audit cycles (default: 4)"
    )
    parser.add_argument(
        "--live", action="store_true",
        help="Use live Claude API (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--mock", action="store_true", default=True,
        help="Use mock connector (default)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Output JSON file path"
    )
    parser.add_argument(
        "--budget", type=float, default=10.0,
        help="Max API budget in USD (default: 10.0)",
    )
    parser.add_argument(
        "--model", type=str, default="claude-sonnet-4-20250514",
        help="Claude model to use",
    )
    parser.add_argument(
        "--api-key", type=str, default=None,
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)",
    )

    args = parser.parse_args()

    if args.live:
        args.mock = False

    result = run_audit(args)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        if args.verbose:
            print(f"\nResults written to {args.output}")
    else:
        if not args.verbose:
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
