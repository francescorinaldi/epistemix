"""
EPISTEMIX v2 — Run Orchestrator

Usage:
  export ANTHROPIC_API_KEY="sk-ant-..."
  python run.py --topic "Kasta Tomb Amphipolis" --country Greece

This is the real thing: it connects to the web,
searches, interprets, and audits — autonomously.

Flow per cycle:
  1. Epistemix generates multilingual queries
  2. Connector sends them to Claude API (with web search)
  3. Claude returns structured findings
  4. Epistemix ingests → updates postulates → re-derives
  5. All modules analyze (citations, disciplines, etc.)
  6. Epistemix generates gap-filling queries
  7. Repeat until convergence or budget exhaustion

Stopping criteria (whichever comes first):
  - Budget exhausted
  - Max cycles reached
  - Coverage score converges (delta < threshold)
"""

from __future__ import annotations
import argparse
import sys
import time
from datetime import datetime

from core import EpistemixEngine, GEOGRAPHIC_LINGUISTIC
from connector import APIConnector, ConnectorConfig
from citation_graph import CitationGraph
from disciplines import DisciplineAnalyzer
from content_analysis import (
    StructuralAbsenceDetector,
    ConvergenceAnalyzer,
    EmptyQueryAnalyzer,
)
from multi_agent import AgentInstitutional, AgentTheoretical, Arbiter
from core import (
    KNOWN_HISTORICAL_FIGURES, KNOWN_PLACES,
    KNOWN_DEITIES_CONCEPTS,
)


def p(text, char="=", w=60):
    print(f"\n{char * w}")
    print(f"  {text}")
    print(f"{char * w}")


def run(
    topic: str,
    country: str,
    discipline: str = "",
    max_cycles: int = 4,
    queries_per_cycle: int = 8,
    total_budget: int = 60,
    model: str = "claude-sonnet-4-5-20250929",
    convergence_threshold: float = 2.0,
    dry_run: bool = False,
):
    """
    Main entry point.

    Args:
        topic: research topic (e.g. "Kasta Tomb Amphipolis")
        country: country of the subject
        discipline: academic discipline
        max_cycles: maximum research cycles
        queries_per_cycle: max API calls per cycle
        total_budget: max API calls total
        model: Claude model to use
        convergence_threshold: stop if coverage delta < this
        dry_run: if True, generate queries but don't call API
    """

    p("EPISTEMIX v2 — Live Research Session")
    print(f"  Topic:      {topic}")
    print(f"  Country:    {country}")
    print(f"  Discipline: {discipline or '(auto-detect)'}")
    print(f"  Max cycles: {max_cycles}")
    print(f"  Budget:     {total_budget} API calls")
    print(f"  Model:      {model}")
    print(f"  Dry run:    {dry_run}")
    print(f"  Started:    {datetime.now().isoformat()}")

    # ── Initialize ──
    engine = EpistemixEngine(
        country=country,
        topic=topic,
        discipline=discipline,
    )

    config = ConnectorConfig(
        model=model,
        budget_per_cycle=queries_per_cycle,
        total_budget=total_budget,
    )
    connector = APIConnector(config)

    if not dry_run and not connector.is_connected:
        print("\n  ⚠️  No API connection available.")
        print("  Set ANTHROPIC_API_KEY or use --dry-run")
        print("  Switching to dry-run mode.\n")
        dry_run = True

    # Auxiliary modules
    citation_graph = CitationGraph()
    citation_graph.register_non_scholars(
        KNOWN_HISTORICAL_FIGURES | KNOWN_PLACES |
        KNOWN_DEITIES_CONCEPTS
    )
    discipline_analyzer = DisciplineAnalyzer()
    empty_query_analyzer = EmptyQueryAnalyzer()

    # ── Cycle 0: Seed queries ──
    p("CYCLE 0: Generating seed queries", "─")
    initial_queries = engine.initialize()
    print(f"  Generated {len(initial_queries)} multilingual queries:")
    for q in initial_queries:
        print(f"    [{q.language}] {q.query}")

    previous_coverage = 0.0

    # ── Main loop ──
    for cycle in range(max_cycles):
        p(f"CYCLE {cycle}: Research", "─")

        # Determine which queries to execute
        if cycle == 0:
            queries = initial_queries
        else:
            queries = engine.pending_queries

        print(f"  Queries to execute: {len(queries)}")

        if dry_run:
            # In dry-run mode, just show queries
            print("  [DRY RUN] Queries that would be executed:")
            for q in queries[:queries_per_cycle]:
                print(f"    [{q.language}] {q.query}")
                print(f"      → {q.rationale}")
            if len(queries) > queries_per_cycle:
                print(
                    f"    ... +{len(queries)-queries_per_cycle}"
                    f" more (budget limited)"
                )

            # Run cycle with no new findings to show evolution
            snapshot = engine.run_cycle()

        else:
            # Execute queries via API
            connector.reset_cycle_counter()
            findings, query_results = connector.execute_batch(
                queries, max_queries=queries_per_cycle
            )

            print(f"  API calls this cycle: {connector.calls_this_cycle}")
            print(f"  Findings received: {len(findings)}")

            # Record empty query results
            for qr in query_results:
                empty_query_analyzer.record_result(qr)

            # Ingest findings
            if findings:
                new_entities = engine.ingest_findings(findings)
                print(f"  New entities discovered: {len(new_entities)}")
                for e in new_entities[:8]:
                    print(f"    • {e}")
                if len(new_entities) > 8:
                    print(f"    ... +{len(new_entities)-8} more")

            # Run audit cycle
            snapshot = engine.run_cycle()

        # Report cycle results
        print(f"\n  📊 Cycle {cycle} results:")
        print(f"     Scholars:     {snapshot.n_postulate_scholars}")
        print(f"     Theories:     {snapshot.n_postulate_theories}")
        print(f"     Institutions: {snapshot.n_postulate_institutions}")
        print(f"     Expectations: {snapshot.n_expectations}")
        print(f"     Met:          {snapshot.n_expectations_met}")
        print(f"     Anomalies:    {snapshot.n_anomalies}")
        print(f"     Coverage:     {snapshot.coverage_score:.0f}%")
        print(f"     Next queries: {snapshot.queries_generated}")

        if not dry_run:
            print(f"\n  💰 API Status:")
            print(f"     {connector.status()}")

        # Check convergence
        delta = abs(snapshot.coverage_score - previous_coverage)
        previous_coverage = snapshot.coverage_score

        if cycle > 0 and delta < convergence_threshold:
            print(
                f"\n  ⏹  Coverage converged (delta={delta:.1f}% "
                f"< {convergence_threshold}%). Stopping."
            )
            break

        if not dry_run and connector.budget_remaining <= 0:
            print("\n  ⏹  Budget exhausted. Stopping.")
            break

    # ── Post-cycle analysis ──
    all_findings = engine.findings

    if all_findings:
        # Citation graph
        p("ANALYSIS: Citation Graph", "─")
        citation_graph.build_from_findings(
            all_findings, engine.postulates.entities
        )
        print(citation_graph.summary())
        cg_anomalies = citation_graph.generate_anomalies()
        for a in cg_anomalies:
            print(f"  {a}")

        # Disciplines
        p("ANALYSIS: Disciplinary Coverage", "─")
        discipline_analyzer.analyze(
            all_findings, engine.postulates
        )
        print(discipline_analyzer.summary())
        da_anomalies = discipline_analyzer.generate_anomalies()
        for a in da_anomalies:
            print(f"  {a}")

        # Empty queries
        if not dry_run and empty_query_analyzer.results:
            p("ANALYSIS: Query Feedback", "─")
            print(empty_query_analyzer.summary())
            eq_anomalies = empty_query_analyzer.generate_anomalies()
            for a in eq_anomalies:
                print(f"  {a}")

        # Multi-agent
        p("ANALYSIS: Multi-Agent Audit", "─")
        alpha = AgentInstitutional(engine.postulates)
        beta = AgentTheoretical(engine.postulates)
        report_a = alpha.audit(all_findings)
        report_b = beta.audit(all_findings)
        arbiter = Arbiter(report_a, report_b)
        arbiter.compare()
        print(arbiter.report())

    # ── Final report ──
    p("CORE ENGINE REPORT", "═")
    print(engine.report())

    # ── Session summary ──
    p("SESSION SUMMARY", "═")
    print(f"  Topic:          {topic}")
    print(f"  Cycles run:     {len(engine.cycle_history)}")
    print(f"  Total findings: {len(engine.findings)}")
    print(f"  Scholars found: {len(engine.postulates.scholars)}")
    print(f"  Theories found: {len(engine.postulates.theories)}")
    print(
        f"  Languages:      "
        f"{', '.join(sorted(engine.postulates.languages_covered))}"
    )

    if not dry_run:
        print(f"  API calls:      {connector.calls_made}")
        print(f"  Est. cost:      ${connector.estimated_cost:.2f}")
        print(f"  Errors:         {len(connector.errors)}")

    print(f"\n  Final coverage:  {previous_coverage:.0f}%")

    if engine.cycle_history:
        print(f"\n  Evolution:")
        print(f"  {'Cycle':>5} {'Scholars':>8} {'Theories':>8} {'Cover':>6}")
        for snap in engine.cycle_history:
            print(
                f"  {snap.cycle:>5} "
                f"{snap.n_postulate_scholars:>8} "
                f"{snap.n_postulate_theories:>8} "
                f"{snap.coverage_score:>5.0f}%"
            )

    print(f"\n  Completed: {datetime.now().isoformat()}")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="EPISTEMIX v2 — Epistemic Research Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (no API calls, shows what would happen):
  python run.py --topic "Kasta Tomb Amphipolis" --country Greece --dry-run

  # Live run with default settings:
  python run.py --topic "Kasta Tomb Amphipolis" --country Greece

  # Live run with custom budget:
  python run.py --topic "Dead Sea Scrolls Cave 12" --country Israel \\
    --discipline "Biblical Archaeology" --cycles 6 --budget 100

  # Use cheaper model:
  python run.py --topic "Antikythera Mechanism" --country Greece \\
    --model claude-haiku-4-5-20251001 --budget 40
        """,
    )

    parser.add_argument(
        "--topic", required=True,
        help="Research topic (e.g. 'Kasta Tomb Amphipolis')"
    )
    parser.add_argument(
        "--country", required=True,
        help="Country of the research subject"
    )
    parser.add_argument(
        "--discipline", default="",
        help="Academic discipline (auto-detected if omitted)"
    )
    parser.add_argument(
        "--cycles", type=int, default=4,
        help="Maximum research cycles (default: 4)"
    )
    parser.add_argument(
        "--queries-per-cycle", type=int, default=8,
        help="Max API calls per cycle (default: 8)"
    )
    parser.add_argument(
        "--budget", type=int, default=60,
        help="Total API call budget (default: 60)"
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-5-20250929",
        help="Claude model to use"
    )
    parser.add_argument(
        "--convergence", type=float, default=2.0,
        help="Stop when coverage delta < this (default: 2.0)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show queries without calling API"
    )

    args = parser.parse_args()

    run(
        topic=args.topic,
        country=args.country,
        discipline=args.discipline,
        max_cycles=args.cycles,
        queries_per_cycle=args.queries_per_cycle,
        total_budget=args.budget,
        model=args.model,
        convergence_threshold=args.convergence,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
