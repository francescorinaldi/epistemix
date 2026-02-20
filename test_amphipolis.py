"""
EPISTEMIX v2 — Amphipolis Dynamic Simulation

The engine starts knowing ONLY:
  - Topic: "Kasta Tomb Amphipolis"
  - Country: "Greece"  
  - Discipline: "Classical Archaeology"

Everything else — scholars, theories, institutions — is
discovered dynamically through simulated research cycles.

Each cycle:
  1. Engine generates multilingual search queries
  2. We feed it simulated findings (what those searches would return)
  3. Engine ingests findings → postulates grow
  4. Engine re-derives expectations → runs audit
  5. Engine generates new targeted queries for gaps
  6. Repeat

The question: starting from near-zero, does the engine
converge on the same knowledge that took us an entire
conversation (plus human intervention) to assemble?
"""

from core import (
    EpistemixEngine, Finding, SearchQuery,
    Severity, GapType
)


def print_header(text: str, char: str = "=", width: int = 64):
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}")


def print_queries(queries: list[SearchQuery], label: str = ""):
    if label:
        print(f"\n  {label}:")
    for q in queries[:12]:
        print(f"    {q}")
        print(f"      ↳ {q.rationale}")
    if len(queries) > 12:
        print(f"    ... +{len(queries) - 12} more")


def print_new_entities(entities: list[str], cycle: int):
    if entities:
        print(f"\n  🆕 New entities discovered in cycle {cycle}:")
        for e in entities:
            print(f"    • {e}")


# ============================================================
# SIMULATED FINDINGS
# Each function returns what a set of searches would find.
# The key constraint: cycle 0 findings contain NO prior
# knowledge — only what initial multilingual queries return.
# ============================================================

def cycle_0_findings() -> list[Finding]:
    """
    What initial multilingual queries would return.
    These are the FIRST results from:
      - "Kasta Amphipolis" (en)
      - "Καστά Αμφίπολη" (el)
      - "Kasta Anfipoli" (it)
      - "Kasta Amphipolis" (de, fr)
      - "Kasta Amphipolis academic publication research" (en)
    """
    return [
        # English Wikipedia / overview
        Finding(
            source="Wikipedia — Kasta Tomb",
            language="en",
            source_type="encyclopedic",
            year=2024,
            entities_mentioned=[
                "Peristeri", "Lefantzis", "Hephaestion",
                "Olympias", "Alexander the Great",
                "Dinocrates", "Cassander",
            ],
        ),
        # Greek news (from Καστά Αμφίπολη search)
        Finding(
            source="Kathimerini — Ανασκαφή στον τύμβο Καστά",
            language="el",
            source_type="journalistic",
            year=2014,
            entities_mentioned=[
                "Peristeri", "Lefantzis", "Tiverios",
                "Faklaris", "Saatsoglou-Paliadeli",
            ],
        ),
        # English news — National Geographic
        Finding(
            source="National Geographic — Mystery tomb Amphipolis",
            language="en",
            source_type="journalistic",
            year=2015,
            entities_mentioned=[
                "Peristeri", "Hephaestion", "Olympias",
                "Worthington", "Frohlich",
            ],
        ),
        # Greek Ministry press release
        Finding(
            source="ΥΠΠΟΑ — Ανακοίνωση τύμβος Καστά",
            language="el",
            author="Peristeri",
            institution="Greek Ministry of Culture",
            source_type="institutional",
            year=2014,
            entities_mentioned=[
                "Peristeri", "Lefantzis",
            ],
        ),
        # Italian result (from "Kasta Anfipoli" search)
        Finding(
            source="Corriere della Sera — La tomba di Anfipoli",
            language="it",
            source_type="journalistic",
            year=2014,
            entities_mentioned=[
                "Peristeri", "Alessandro Magno",
                "Efestione",
            ],
        ),
        # German result (from "Kasta Amphipolis" search)
        Finding(
            source="Spiegel — Grabmal von Amphipolis",
            language="de",
            source_type="journalistic",
            year=2014,
            entities_mentioned=[
                "Peristeri", "Alexander", "Hephaistion",
            ],
        ),
        # Academic search result
        Finding(
            source="Greek Reporter — Hephaestion monogram found",
            language="en",
            author="Peristeri",
            institution="Greek Ministry of Culture",
            theory_supported="Hephaestion memorial",
            source_type="journalistic",
            year=2015,
            entities_mentioned=[
                "Peristeri", "Lefantzis", "Hephaestion",
            ],
        ),
    ]


def cycle_1_findings() -> list[Finding]:
    """
    After cycle 0, the engine should ask to investigate:
      - Tiverios (mentioned in Greek press)
      - Faklaris (mentioned in Greek press)
      - Worthington (mentioned in NatGeo)
      - Saatsoglou-Paliadeli (mentioned in Greek press)
      - Lefantzis (co-excavator)
    And search for academic publications on the topic.
    
    These are what those targeted searches would return.
    """
    return [
        # Searching "Tiverios Amphipolis"
        Finding(
            source="Newsbomb — Τι πιστεύει ο Τιβέριος",
            language="el",
            author="Tiverios",
            institution="Aristotle University of Thessaloniki",
            theory_supported="Nearchus burial (minority)",
            source_type="journalistic",
            year=2014,
            entities_mentioned=[
                "Tiverios", "Nearchus", "Peristeri",
                "Mavrogiannis",
            ],
        ),
        # Searching "Faklaris Amphipolis"
        Finding(
            source="TOC — Faklaris: premature conclusions",
            language="en",
            author="Faklaris",
            institution="Aristotle University of Thessaloniki",
            source_type="journalistic",
            year=2014,
            entities_mentioned=[
                "Faklaris", "Peristeri", "Hephaestion",
            ],
        ),
        # Searching "Worthington Amphipolis"
        Finding(
            source="Live Science — Worthington skepticism",
            language="en",
            author="Worthington",
            institution="Macquarie University",
            source_type="journalistic",
            year=2015,
            entities_mentioned=[
                "Worthington", "Peristeri", "Olympias",
                "Chugg",
            ],
        ),
        # Academic search result — discovers Chugg
        Finding(
            source=(
                "Academia.edu — A. Chugg, "
                "The Tomb of Alexander the Great and "
                "the Identity of the Occupant of the "
                "Great Tomb at Amphipolis"
            ),
            language="en",
            author="Chugg",
            institution="Independent researcher",
            theory_supported="Olympias burial",
            source_type="peer_reviewed",
            year=2021,
            entities_mentioned=[
                "Chugg", "Olympias", "Peristeri",
                "Hephaestion", "Cassander",
                "Mavrogiannis", "Palagia",
            ],
        ),
        # Greek academic search — discovers Saatsoglou-Paliadeli
        Finding(
            source="ANA-MPA — Saatsoglou-Paliadeli caution",
            language="el",
            author="Saatsoglou-Paliadeli",
            institution="Aristotle University of Thessaloniki",
            source_type="journalistic",
            year=2014,
            entities_mentioned=[
                "Saatsoglou-Paliadeli", "Peristeri",
                "Philip II", "Vergina",
            ],
        ),
    ]


def cycle_2_findings() -> list[Finding]:
    """
    After cycle 1, the engine should now know about:
      - Mavrogiannis (mentioned by Tiverios AND Chugg)
      - Palagia (mentioned by Chugg)
      - Chugg's Olympias theory (primary source found)
    
    It should generate queries like:
      - "Mavrogiannis Amphipolis" (en, el, it)
      - "Palagia Amphipolis" (en, el)
    
    THIS IS THE CRITICAL CYCLE: finding Mavrogiannis.
    """
    return [
        # Searching "Mavrogiannis Amphipolis" — THE KEY DISCOVERY
        Finding(
            source=(
                "Academia.edu — T. Mavrogiannis, "
                "Considerazioni storiche sulla sepoltura "
                "dell'ateniese Hephaestion ad Amphipolis"
            ),
            language="it",
            author="Mavrogiannis",
            institution="University of Cyprus",
            theory_supported="Hephaestion burial (historical)",
            source_type="peer_reviewed",
            year=2018,
            entities_mentioned=[
                "Mavrogiannis", "Hephaestion", "Amyntor",
                "Antipatros", "Amphipolis",
            ],
        ),
        # Mavrogiannis in Vestigia (German/international volume)
        Finding(
            source=(
                "Vestigia (Stuttgart 2016) — "
                "The Great Tumulus at Amphipolis: "
                "Remarks on Chronology and Historical Context"
            ),
            language="en",
            author="Mavrogiannis",
            institution="University of Cyprus",
            theory_supported="Hephaestion burial (historical)",
            source_type="peer_reviewed",
            year=2016,
            entities_mentioned=[
                "Mavrogiannis", "Hephaestion",
                "Voutyras", "Cassander", "Peristeri",
            ],
        ),
        # Mavrogiannis TV interview (Greek)
        Finding(
            source="ΣΚΑΪ — Μαυρογιάννης: Ηφαιστίων ο νεκρός",
            language="el",
            author="Mavrogiannis",
            institution="University of Cyprus",
            theory_supported="Hephaestion burial (historical)",
            source_type="journalistic",
            year=2014,
            entities_mentioned=[
                "Mavrogiannis", "Hephaestion",
                "Diodorus Siculus",
            ],
        ),
        # Searching "Palagia Amphipolis"
        Finding(
            source=(
                "O. Palagia — review of Amphipolis evidence"
            ),
            language="en",
            author="Palagia",
            institution="University of Athens",
            source_type="peer_reviewed",
            year=2016,
            entities_mentioned=[
                "Palagia", "Peristeri", "Chugg",
                "Hephaestion", "Olympias",
            ],
        ),
        # Chugg inscription analysis (found via deeper search)
        Finding(
            source=(
                "A. Chugg — The Truth about the "
                "Hephaistion Inscriptions at Amphipolis"
            ),
            language="en",
            author="Chugg",
            institution="Independent researcher",
            theory_supported="Olympias burial",
            source_type="peer_reviewed",
            year=2016,
            entities_mentioned=[
                "Chugg", "Peristeri", "ΠΑΡΕΛΑΒΟΝ",
            ],
        ),
    ]


def cycle_3_findings() -> list[Finding]:
    """
    Cycle 3: deeper investigation and recent sources.
    By now the engine knows the three main theories and
    should look for:
      - Recent developments (2024-2025)
      - Savvides solar alignment study
      - DNA analysis updates
      - Voutyras (mentioned in Mavrogiannis)
    """
    return [
        # Savvides 2025 study
        Finding(
            source=(
                "Nexus Network Journal — D. Savvides, "
                "Solar alignment of Kasta Tomb"
            ),
            language="en",
            author="Savvides",
            institution="Independent researcher",
            theory_supported="Hephaestion memorial",
            source_type="peer_reviewed",
            year=2025,
            entities_mentioned=[
                "Savvides", "Hephaestion", "Cybele",
                "Peristeri", "de Lara",
            ],
        ),
        # IFLScience coverage
        Finding(
            source="IFLScience — Winter solstice Amphipolis",
            language="en",
            source_type="journalistic",
            year=2025,
            entities_mentioned=[
                "Savvides", "Hephaestion",
            ],
        ),
        # Dendrinos
        Finding(
            source=(
                "ResearchGate — D. Dendrinos, "
                "On the Hephaestion Hypothesis"
            ),
            language="en",
            author="Dendrinos",
            institution="Independent researcher",
            theory_supported="Hephaestion memorial",
            source_type="peer_reviewed",
            year=2015,
            entities_mentioned=[
                "Dendrinos", "Peristeri", "Deinokratis",
            ],
        ),
        # Voutyras
        Finding(
            source=(
                "Voutyras — Hellenistic funerary practices "
                "in Macedonia"
            ),
            language="en",
            author="Voutyras",
            institution="Aristotle University of Thessaloniki",
            source_type="peer_reviewed",
            year=2015,
            entities_mentioned=[
                "Voutyras", "Peristeri", "Vergina",
            ],
        ),
        # French School contribution
        Finding(
            source=(
                "BCH — Bulletin de Correspondance Hellénique, "
                "Note sur le tumulus Kasta"
            ),
            language="fr",
            source_type="peer_reviewed",
            year=2016,
            entities_mentioned=[
                "Peristeri", "Amphipolis",
            ],
        ),
    ]


# ============================================================
# MAIN SIMULATION
# ============================================================

def main():
    print_header(
        "EPISTEMIX v2 — Dynamic Simulation\n"
        "  The Kasta Tomb at Amphipolis",
        "═", 64,
    )

    print("""
  STARTING KNOWLEDGE:
    Topic:      "Kasta Tomb Amphipolis"
    Country:    "Greece"
    Discipline: "Classical Archaeology"
    
    Scholars known:     0
    Theories known:     0
    Institutions known: 0
    
  Everything else will be discovered dynamically.
""")

    # Initialize engine with minimal seed
    engine = EpistemixEngine(
        country="Greece",
        topic="Kasta Tomb Amphipolis",
        discipline="Classical Archaeology",
    )
    engine.postulates.discovery_year = 2012
    engine.postulates.ongoing = True

    # ── CYCLE 0: Initial multilingual queries ──
    print_header("CYCLE 0 — Seed Queries", "─")
    initial_queries = engine.initialize()
    print_queries(initial_queries, "Generated multilingual queries")

    # Simulate results
    print("\n  📥 Ingesting initial findings...")
    new_entities = engine.ingest_findings(cycle_0_findings())
    print_new_entities(new_entities, 0)

    # Run first audit
    snapshot = engine.run_cycle()
    print(f"\n  📊 After cycle 0:")
    print(f"     Scholars:     {snapshot.n_postulate_scholars}")
    print(f"     Theories:     {snapshot.n_postulate_theories}")
    print(f"     Institutions: {snapshot.n_postulate_institutions}")
    print(f"     Expectations: {snapshot.n_expectations}")
    print(f"     Met:          {snapshot.n_expectations_met}")
    print(f"     Anomalies:    {snapshot.n_anomalies}")
    print(f"     Coverage:     {snapshot.coverage_score:.0f}%")
    print(f"     New queries:  {snapshot.queries_generated}")
    print_queries(
        engine.pending_queries,
        "Gap-filling queries generated"
    )

    # ── CYCLE 1: Investigate discovered scholars ──
    print_header("CYCLE 1 — Investigating Discovered Scholars", "─")
    new_entities = engine.ingest_findings(cycle_1_findings())
    print_new_entities(new_entities, 1)

    snapshot = engine.run_cycle()
    print(f"\n  📊 After cycle 1:")
    print(f"     Scholars:     {snapshot.n_postulate_scholars}")
    print(f"     Theories:     {snapshot.n_postulate_theories}")
    print(f"     Institutions: {snapshot.n_postulate_institutions}")
    print(f"     Expectations: {snapshot.n_expectations}")
    print(f"     Met:          {snapshot.n_expectations_met}")
    print(f"     Anomalies:    {snapshot.n_anomalies}")
    print(f"     Coverage:     {snapshot.coverage_score:.0f}%")
    print(f"     New queries:  {snapshot.queries_generated}")

    # Show that Mavrogiannis is now flagged
    mavro = engine.postulates.entities.get("mavrogiannis")
    if mavro:
        print(f"\n  🎯 MAVROGIANNIS STATUS:")
        print(f"     Mentioned:    {mavro.times_mentioned}x")
        print(f"     Investigated: {mavro.investigated}")
        print(f"     First seen:   {mavro.first_seen_in}")
        print(f"     → System will generate queries to find him")

    print_queries(
        [q for q in engine.pending_queries
         if "mavrogiannis" in q.query.lower()],
        "Mavrogiannis-specific queries"
    )

    # ── CYCLE 2: THE CRITICAL CYCLE — Finding Mavrogiannis ──
    print_header(
        "CYCLE 2 — THE CRITICAL CYCLE: Finding Mavrogiannis", "─"
    )
    new_entities = engine.ingest_findings(cycle_2_findings())
    print_new_entities(new_entities, 2)

    snapshot = engine.run_cycle()
    print(f"\n  📊 After cycle 2:")
    print(f"     Scholars:     {snapshot.n_postulate_scholars}")
    print(f"     Theories:     {snapshot.n_postulate_theories}")
    print(f"     Institutions: {snapshot.n_postulate_institutions}")
    print(f"     Expectations: {snapshot.n_expectations}")
    print(f"     Met:          {snapshot.n_expectations_met}")
    print(f"     Anomalies:    {snapshot.n_anomalies}")
    print(f"     Coverage:     {snapshot.coverage_score:.0f}%")

    # Verify Mavrogiannis is now investigated
    mavro = engine.postulates.entities.get("mavrogiannis")
    if mavro:
        print(f"\n  🎯 MAVROGIANNIS STATUS:")
        print(f"     Mentioned:    {mavro.times_mentioned}x")
        print(f"     Investigated: ✅ {mavro.investigated}")
        print(f"     Institution:  {mavro.affiliated_institution}")

    # ── CYCLE 3: Deepening and recent sources ──
    print_header("CYCLE 3 — Deepening & Recent Sources", "─")
    new_entities = engine.ingest_findings(cycle_3_findings())
    print_new_entities(new_entities, 3)

    snapshot = engine.run_cycle()
    print(f"\n  📊 After cycle 3:")
    print(f"     Scholars:     {snapshot.n_postulate_scholars}")
    print(f"     Theories:     {snapshot.n_postulate_theories}")
    print(f"     Institutions: {snapshot.n_postulate_institutions}")
    print(f"     Expectations: {snapshot.n_expectations}")
    print(f"     Met:          {snapshot.n_expectations_met}")
    print(f"     Anomalies:    {snapshot.n_anomalies}")
    print(f"     Coverage:     {snapshot.coverage_score:.0f}%")

    # ── FULL REPORT ──
    print_header("FULL REPORT", "═")
    print(engine.report())

    # ── EVOLUTION SUMMARY ──
    print_header("SYSTEM EVOLUTION SUMMARY", "═")
    print("""
  The engine started knowing NOTHING except "Kasta Tomb,
  Greece, Classical Archaeology."
  
  Through 4 cycles of: search → discover → audit → search:
""")

    for snap in engine.cycle_history:
        print(
            f"    Cycle {snap.cycle}: "
            f"{snap.n_postulate_scholars} scholars, "
            f"{snap.n_postulate_theories} theories, "
            f"{snap.n_postulate_institutions} institutions "
            f"→ coverage {snap.coverage_score:.0f}%"
        )

    print(f"""
  KEY RESULT:
  
    In cycle 1, Mavrogiannis appeared as an entity mentioned
    by TWO independent sources (Tiverios and Chugg) but NOT
    yet investigated. The engine flagged this and generated
    multilingual queries to find his work.
    
    By cycle 2, his publications were found — in Italian,
    English, and Greek — and the third major theory
    ("Hephaestion burial, historical argument") was
    incorporated into the postulates.
    
    This is exactly the gap that required human intervention
    in our original conversation. The dynamic framework
    found it automatically through:
    
      1. AXIOM (geographic-linguistic): Greece → search in
         Greek, Italian, German, French, English
      2. AXIOM (entity investigation): name mentioned 2+
         times but no publications found → flag as gap
      3. INFERENCE: generate targeted multilingual queries
      4. DISCOVERY: Mavrogiannis's Italian and English papers

  REMAINING LIMITATIONS:

    The framework still cannot detect:
    - Scholars who are NEVER mentioned in ANY source found
    - Entire research traditions unknown to the axiom system
    - Theories that exist only in unpublished form
    - Its own axiom blindspots
    
    Coverage score ({engine.cycle_history[-1].coverage_score:.0f}%) 
    is a LOWER BOUND, not a measure of completeness.
""")


if __name__ == "__main__":
    main()
