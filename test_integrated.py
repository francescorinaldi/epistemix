"""
EPISTEMIX v2 — Full Integrated Test
All modules working together on the Amphipolis case.

Modules:
  - core.py: dynamic postulates, cyclic engine
  - citation_graph.py: who cites whom, school detection
  - disciplines.py: sub-discipline specialist coverage
  - content_analysis.py: structural gaps, convergence, empty queries
  - multi_agent.py: dual-agent cross-audit

Flow:
  Cycle 0: seed queries (multilingual) → initial findings
  Cycle 1: investigate discovered scholars → find Mavrogiannis
  Cycle 2: investigate Mavrogiannis → third theory emerges
  Cycle 3: deepen + recent sources → final audit
  Final: all modules produce combined report
"""

from core import EpistemixEngine, Finding
from citation_graph import CitationGraph
from disciplines import DisciplineAnalyzer
from content_analysis import (
    StructuralAbsenceDetector, StructuralFact,
    ConvergenceAnalyzer, TheoryPosition,
    EmptyQueryAnalyzer, QueryResult,
)
from multi_agent import AgentInstitutional, AgentTheoretical, Arbiter


# ============================================================
# SIMULATED FINDINGS (same as before, kept compact)
# ============================================================

def cycle_0():
    return [
        Finding(source="Wikipedia — Kasta Tomb", language="en",
                source_type="encyclopedic", year=2024,
                entities_mentioned=["Peristeri","Lefantzis","Hephaestion",
                    "Olympias","Alexander the Great","Dinocrates","Cassander"]),
        Finding(source="Kathimerini — Ανασκαφή τύμβο Καστά", language="el",
                source_type="journalistic", year=2014,
                entities_mentioned=["Peristeri","Lefantzis","Tiverios",
                    "Faklaris","Saatsoglou-Paliadeli"]),
        Finding(source="NatGeo — Mystery tomb", language="en",
                source_type="journalistic", year=2015,
                entities_mentioned=["Peristeri","Hephaestion","Olympias",
                    "Worthington","Frohlich"]),
        Finding(source="ΥΠΠΟΑ — Ανακοίνωση", language="el",
                author="Peristeri", institution="Greek Ministry of Culture",
                source_type="institutional", year=2014,
                entities_mentioned=["Peristeri","Lefantzis"]),
        Finding(source="Corriere della Sera — Anfipoli", language="it",
                source_type="journalistic", year=2014,
                entities_mentioned=["Peristeri","Alessandro Magno","Efestione"]),
        Finding(source="Spiegel — Grabmal Amphipolis", language="de",
                source_type="journalistic", year=2014,
                entities_mentioned=["Peristeri","Alexander","Hephaistion"]),
        Finding(source="Greek Reporter — monogram", language="en",
                author="Peristeri", institution="Greek Ministry of Culture",
                theory_supported="Hephaestion memorial",
                source_type="journalistic", year=2015,
                entities_mentioned=["Peristeri","Lefantzis","Hephaestion"]),
    ]

def cycle_1():
    return [
        Finding(source="Newsbomb — Τιβέριος", language="el",
                author="Tiverios", institution="Aristotle University of Thessaloniki",
                theory_supported="Nearchus burial (minority)",
                source_type="journalistic", year=2014,
                entities_mentioned=["Tiverios","Nearchus","Peristeri","Mavrogiannis"]),
        Finding(source="TOC — Faklaris caution", language="en",
                author="Faklaris", institution="Aristotle University of Thessaloniki",
                source_type="journalistic", year=2014,
                entities_mentioned=["Faklaris","Peristeri","Hephaestion"]),
        Finding(source="Live Science — Worthington", language="en",
                author="Worthington", institution="Macquarie University",
                source_type="journalistic", year=2015,
                entities_mentioned=["Worthington","Peristeri","Olympias","Chugg"]),
        Finding(source="Chugg — Identity of Occupant", language="en",
                author="Chugg", institution="Independent researcher",
                theory_supported="Olympias burial",
                source_type="peer_reviewed", year=2021,
                entities_mentioned=["Chugg","Olympias","Peristeri",
                    "Hephaestion","Cassander","Mavrogiannis","Palagia"]),
        Finding(source="ANA-MPA — Saatsoglou-Paliadeli", language="el",
                author="Saatsoglou-Paliadeli",
                institution="Aristotle University of Thessaloniki",
                source_type="journalistic", year=2014,
                entities_mentioned=["Saatsoglou-Paliadeli","Peristeri",
                    "Philip II","Vergina"]),
    ]

def cycle_2():
    return [
        Finding(source="Academia.edu — Mavrogiannis, Considerazioni storiche",
                language="it", author="Mavrogiannis",
                institution="University of Cyprus",
                theory_supported="Hephaestion burial (historical)",
                source_type="peer_reviewed", year=2018,
                entities_mentioned=["Mavrogiannis","Hephaestion","Amyntor",
                    "Antipatros","Amphipolis"]),
        Finding(source="Vestigia — Mavrogiannis, Great Tumulus Remarks",
                language="en", author="Mavrogiannis",
                institution="University of Cyprus",
                theory_supported="Hephaestion burial (historical)",
                source_type="peer_reviewed", year=2016,
                entities_mentioned=["Mavrogiannis","Hephaestion","Voutyras",
                    "Cassander","Peristeri"]),
        Finding(source="ΣΚΑΪ — Μαυρογιάννης interview", language="el",
                author="Mavrogiannis", institution="University of Cyprus",
                theory_supported="Hephaestion burial (historical)",
                source_type="journalistic", year=2014,
                entities_mentioned=["Mavrogiannis","Hephaestion","Diodorus Siculus"]),
        Finding(source="Palagia — review of evidence", language="en",
                author="Palagia", institution="University of Athens",
                source_type="peer_reviewed", year=2016,
                entities_mentioned=["Palagia","Peristeri","Chugg",
                    "Hephaestion","Olympias"]),
        Finding(source="Chugg — Hephaistion Inscriptions", language="en",
                author="Chugg", institution="Independent researcher",
                theory_supported="Olympias burial",
                source_type="peer_reviewed", year=2016,
                entities_mentioned=["Chugg","Peristeri","ΠΑΡΕΛΑΒΟΝ"]),
    ]

def cycle_3():
    return [
        Finding(source="Nexus Network Journal — Savvides solar alignment",
                language="en", author="Savvides",
                institution="Independent researcher",
                theory_supported="Hephaestion memorial",
                source_type="peer_reviewed", year=2025,
                entities_mentioned=["Savvides","Hephaestion","Cybele",
                    "Peristeri","de Lara"]),
        Finding(source="IFLScience — solstice Amphipolis", language="en",
                source_type="journalistic", year=2025,
                entities_mentioned=["Savvides","Hephaestion"]),
        Finding(source="Dendrinos — Hephaestion Hypothesis", language="en",
                author="Dendrinos", institution="Independent researcher",
                theory_supported="Hephaestion memorial",
                source_type="peer_reviewed", year=2015,
                entities_mentioned=["Dendrinos","Peristeri","Deinokratis"]),
        Finding(source="Voutyras — Hellenistic funerary", language="en",
                author="Voutyras",
                institution="Aristotle University of Thessaloniki",
                source_type="peer_reviewed", year=2015,
                entities_mentioned=["Voutyras","Peristeri","Vergina"]),
        Finding(source="BCH — Note sur Kasta", language="fr",
                source_type="peer_reviewed", year=2016,
                entities_mentioned=["Peristeri","Amphipolis"]),
    ]


# ============================================================
# MAIN
# ============================================================

def p(text, char="=", w=60):
    print(f"\n{char * w}")
    print(f"  {text}")
    print(f"{char * w}")


def main():
    p("EPISTEMIX v2 — FULL INTEGRATED TEST")
    print("  Starting from: topic + country only")
    print("  Modules: core + citations + disciplines")
    print("           + content + multi-agent")

    # Initialize engine
    engine = EpistemixEngine(
        country="Greece",
        topic="Kasta Tomb Amphipolis",
        discipline="Classical Archaeology",
    )
    engine.postulates.discovery_year = 2012
    engine.postulates.ongoing = True

    # Run 4 cycles
    all_findings_by_cycle = [cycle_0, cycle_1, cycle_2, cycle_3]
    cycle_names = [
        "Seed (multilingual)",
        "Investigate scholars",
        "CRITICAL: Finding Mavrogiannis",
        "Deepen + recent",
    ]

    for i, (get_findings, name) in enumerate(
        zip(all_findings_by_cycle, cycle_names)
    ):
        p(f"CYCLE {i}: {name}", "─")
        if i == 0:
            queries = engine.initialize()
            print(f"  Initial queries: {len(queries)}")
            for q in queries[:4]:
                print(f"    [{q.language}] {q.query}")
            if len(queries) > 4:
                print(f"    ... +{len(queries)-4} more")

        new = engine.ingest_findings(get_findings())
        snap = engine.run_cycle()

        print(f"  New entities: {len(new)}")
        print(f"  Scholars: {snap.n_postulate_scholars}")
        print(f"  Theories: {snap.n_postulate_theories}")
        print(f"  Coverage: {snap.coverage_score:.0f}%")
        print(f"  Anomalies: {snap.n_anomalies}")
        print(f"  Next queries: {snap.queries_generated}")

        # Check Mavrogiannis status
        m = engine.postulates.entities.get("mavrogiannis")
        if m:
            status = "✅ investigated" if m.investigated else f"⚠️ mentioned {m.times_mentioned}x, NOT investigated"
            print(f"  Mavrogiannis: {status}")

    # ============================================
    # POST-CYCLE ANALYSIS: All modules
    # ============================================
    all_findings = engine.findings

    # --- CITATION GRAPH ---
    p("MODULE: Citation Graph", "─")
    cg = CitationGraph()
    from core import KNOWN_HISTORICAL_FIGURES, KNOWN_PLACES, KNOWN_DEITIES_CONCEPTS
    cg.register_non_scholars(
        KNOWN_HISTORICAL_FIGURES | KNOWN_PLACES | KNOWN_DEITIES_CONCEPTS
    )
    cg.build_from_findings(all_findings, engine.postulates.entities)
    print(cg.summary())
    cg_anomalies = cg.generate_anomalies()
    if cg_anomalies:
        print("\nAnomalies:")
        for a in cg_anomalies:
            print(f"  {a}")

    # --- DISCIPLINES ---
    p("MODULE: Disciplinary Coverage", "─")
    da = DisciplineAnalyzer()
    da.analyze(all_findings, engine.postulates)
    print(da.summary())
    da_anomalies = da.generate_anomalies()
    if da_anomalies:
        print("\nAnomalies:")
        for a in da_anomalies:
            print(f"  {a}")

    # --- STRUCTURAL ABSENCES ---
    p("MODULE: Structural Absences", "─")
    sad = StructuralAbsenceDetector()
    sad.register_fact(StructuralFact(
        category="Individuals in tomb",
        count=5,
        items=[
            "woman ~60 years (Olympias candidate)",
            "man 35-45 (first)",
            "man 35-45 (second)",
            "newborn infant",
            "cremated individual",
        ],
        source="Osteological report 2015",
    ))
    sad.register_fact(StructuralFact(
        category="Inscriptions with ΠΑΡΕΛΑΒΟΝ",
        count=3,
        items=[
            "inscription block 1",
            "inscription block 2",
            "inscription block 3",
        ],
        source="Peristeri epigraphy report",
    ))
    gaps = sad.check_coverage(engine.postulates.theories)
    sa_anomalies = sad.generate_anomalies()
    for a in sa_anomalies:
        print(f"  {a}")

    # --- CONVERGENCE ---
    p("MODULE: Convergence / Contradiction", "─")
    ca = ConvergenceAnalyzer()
    ca.register_position(TheoryPosition(
        "Hephaestion memorial", "Who is the primary occupant?",
        "Hephaestion", "Monogram + inscriptions", "Peristeri"))
    ca.register_position(TheoryPosition(
        "Olympias burial", "Who is the primary occupant?",
        "Olympias", "Woman's age + mosaic + Cassander", "Chugg"))
    ca.register_position(TheoryPosition(
        "Hephaestion burial (historical)", "Who is the primary occupant?",
        "Hephaestion", "Historical argument + Amyntor", "Mavrogiannis"))
    ca.register_position(TheoryPosition(
        "Nearchus burial", "Who is the primary occupant?",
        "Nearchus", "Amphipolis naval connection", "Tiverios"))
    ca.register_position(TheoryPosition(
        "Hephaestion memorial", "Who commissioned the tomb?",
        "Alexander the Great", "Diodorus account", "Peristeri"))
    ca.register_position(TheoryPosition(
        "Olympias burial", "Who commissioned the tomb?",
        "Cassander (repurposed)", "Cut inscription blocks", "Chugg"))
    ca.register_position(TheoryPosition(
        "Hephaestion burial (historical)", "Who commissioned the tomb?",
        "Antipater regime", "Political context 322-318 BC", "Mavrogiannis"))
    print(ca.summary())
    ca_anomalies = ca.generate_anomalies()
    if ca_anomalies:
        print("\nAnomalies:")
        for a in ca_anomalies:
            print(f"  {a}")

    # --- MULTI-AGENT ---
    p("MODULE: Multi-Agent Audit", "─")
    alpha = AgentInstitutional(engine.postulates)
    beta = AgentTheoretical(engine.postulates)
    report_a = alpha.audit(all_findings)
    report_b = beta.audit(all_findings)
    arbiter = Arbiter(report_a, report_b)
    arbiter.compare()
    print(arbiter.report())

    # ============================================
    # FINAL SYNTHESIS
    # ============================================
    p("FINAL SYNTHESIS", "═")

    # Collect ALL anomalies from all modules
    all_anomalies = (
        engine.all_anomalies +
        cg_anomalies +
        da_anomalies +
        sa_anomalies +
        ca_anomalies +
        arbiter.combined_anomalies
    )

    # Deduplicate by description prefix
    seen = set()
    unique = []
    for a in all_anomalies:
        key = a.description[:50]
        if key not in seen:
            seen.add(key)
            unique.append(a)

    # Sort by severity
    unique.sort(key=lambda a: a.severity.value, reverse=True)

    print(f"\n  Total unique anomalies across all modules: {len(unique)}")
    print(f"\n  By severity:")
    for sev_name in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = sum(1 for a in unique if a.severity.name == sev_name)
        if count:
            print(f"    {sev_name}: {count}")

    print(f"\n  By type:")
    from collections import Counter
    type_counts = Counter(a.gap_type.value for a in unique)
    for gtype, count in type_counts.most_common():
        print(f"    {gtype}: {count}")

    # Core engine evolution
    print(f"\n  Engine evolution:")
    print(f"  {'Cycle':>5} {'Scholars':>8} {'Theories':>8} {'Cover':>6}")
    for snap in engine.cycle_history:
        print(f"  {snap.cycle:>5} {snap.n_postulate_scholars:>8} "
              f"{snap.n_postulate_theories:>8} {snap.coverage_score:>5.0f}%")

    # Final scores
    core_cov = engine.cycle_history[-1].coverage_score
    multi_cov = arbiter.combined_score()
    print(f"\n  Core engine coverage:   {core_cov:.0f}%")
    print(f"  Multi-agent coverage:   {multi_cov:.0f}%")
    print(f"  Discrepancies found:    {len(arbiter.discrepancies)}")
    print(f"  Discipline gaps:        {len(da_anomalies)}")
    print(f"  Structural gaps:        {len(sa_anomalies)}")

    print(f"""
  The integrated system finds {len(unique)} unique issues
  that the original conversation — without the framework —
  would have missed entirely, except for the one gap
  (Mavrogiannis) that required human intervention.

  The framework does not claim completeness. It claims
  STRUCTURED INCOMPLETENESS: a systematic map of what
  is known to be missing, derived from formal axioms
  rather than intuition.

  What remains invisible: gaps in categories the axioms
  don't model. The only mitigation: external review,
  additional agents with different axioms, or a human
  who asks the right question at the right time.
""")


if __name__ == "__main__":
    main()
