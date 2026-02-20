"""
EPISTEMIX v2 — Content Analysis Module

Three components:

1. STRUCTURAL ABSENCES
   If findings mention N items of a type but research
   addresses only M < N, the remainder are gaps.
   Example: 5 individuals found in tomb, theories discuss 1.

2. CONVERGENCE / CONTRADICTION
   Measures agreement between sources. Two sources that
   agree add less new information than two that disagree.
   A debate with only agreement suggests missing dissent.
   A debate with only disagreement suggests missing synthesis.

3. EMPTY QUERY FEEDBACK
   When a query returns no results, that is information.
   "Mavrogiannis Amphipolis" returning nothing in German
   tells us something different from the same query in
   Italian returning three papers.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from core import (
    Finding, DynamicPostulates, Anomaly,
    Severity, GapType, SearchQuery,
)


# ============================================================
# PART 1: STRUCTURAL ABSENCES
# ============================================================

@dataclass
class StructuralFact:
    """A quantitative fact extracted from findings."""
    category: str       # e.g. "individuals in tomb"
    count: int          # e.g. 5
    items: list[str]    # e.g. ["woman ~60", "man 35-45", ...]
    source: str         # where this fact was found


@dataclass
class StructuralGap:
    """A gap between stated facts and research coverage."""
    fact: StructuralFact
    addressed_count: int
    addressed_items: list[str]
    missing_count: int
    severity: Severity


class StructuralAbsenceDetector:
    """
    Detects when findings state quantitative facts that
    are not fully addressed by the research.
    """

    def __init__(self):
        self.facts: list[StructuralFact] = []
        self.gaps: list[StructuralGap] = []

    def register_fact(self, fact: StructuralFact):
        """Manually register a structural fact."""
        self.facts.append(fact)

    def extract_facts_from_findings(
        self, findings: list[Finding]
    ):
        """
        Attempt to auto-extract quantitative facts.
        This is heuristic — looks for numeric patterns.
        """
        # Keywords suggesting countable items
        count_patterns = {
            "individuals": [
                "individuals", "persons", "bodies",
                "skeletons", "remains found",
            ],
            "chambers": [
                "chambers", "rooms", "compartments",
            ],
            "phases": [
                "phases", "construction phases",
                "building phases",
            ],
            "inscriptions": [
                "inscriptions found", "texts found",
            ],
        }

        corpus = " ".join(
            f.source.lower() + " " +
            " ".join(e.lower() for e in f.entities_mentioned)
            for f in findings
        )

        for category, keywords in count_patterns.items():
            for kw in keywords:
                if kw in corpus:
                    # Found reference but can't extract count
                    # automatically — flag for attention
                    pass

    def check_coverage(
        self, theories: list[str]
    ) -> list[StructuralGap]:
        """
        Check if registered facts are fully covered by
        theories and findings.
        """
        self.gaps = []

        for fact in self.facts:
            # Count how many items are addressed
            addressed = []
            theories_lower = [t.lower() for t in theories]

            for item in fact.items:
                item_lower = item.lower()
                # Check if any theory mentions this item
                for theory in theories_lower:
                    if any(
                        word in theory
                        for word in item_lower.split()
                        if len(word) > 3
                    ):
                        addressed.append(item)
                        break

            missing = fact.count - len(addressed)

            if missing > 0:
                severity = Severity.MEDIUM
                if missing > fact.count / 2:
                    severity = Severity.HIGH
                if missing == fact.count:
                    severity = Severity.CRITICAL

                self.gaps.append(StructuralGap(
                    fact=fact,
                    addressed_count=len(addressed),
                    addressed_items=addressed,
                    missing_count=missing,
                    severity=severity,
                ))

        return self.gaps

    def generate_anomalies(self) -> list[Anomaly]:
        anomalies = []
        for gap in self.gaps:
            unaddressed = [
                item for item in gap.fact.items
                if item not in gap.addressed_items
            ]
            anomalies.append(Anomaly(
                description=(
                    f"{gap.fact.category}: "
                    f"{gap.fact.count} stated but only "
                    f"{gap.addressed_count} addressed by "
                    f"theories. Unexamined: "
                    f"{', '.join(unaddressed)}"
                ),
                gap_type=GapType.VOICE,
                severity=gap.severity,
                recommendation=(
                    f"Search for research on: "
                    f"{', '.join(unaddressed)}"
                ),
            ))
        return anomalies


# ============================================================
# PART 2: CONVERGENCE / CONTRADICTION
# ============================================================

@dataclass
class TheoryPosition:
    """A theory's position on a specific question."""
    theory: str
    question: str     # e.g. "who is buried?"
    answer: str       # e.g. "Olympias"
    evidence: str     # brief evidence summary
    source_author: str


class ConvergenceAnalyzer:
    """
    Tracks positions of different theories on shared
    questions. Measures agreement and disagreement.
    """

    def __init__(self):
        self.positions: list[TheoryPosition] = []
        self.questions: dict[str, list[TheoryPosition]] = (
            defaultdict(list)
        )

    def register_position(self, position: TheoryPosition):
        self.positions.append(position)
        self.questions[position.question].append(position)

    def analyze(self) -> dict:
        """
        For each question, determine:
        - How many distinct answers exist
        - Whether there is consensus or disagreement
        - Information value (more disagreement = more info)
        """
        results = {}

        for question, positions in self.questions.items():
            answers = defaultdict(list)
            for p in positions:
                answers[p.answer.lower()].append(p)

            n_distinct = len(answers)
            n_total = len(positions)

            # Consensus ratio: 1.0 = everyone agrees,
            # 0.0 = everyone disagrees
            if n_total <= 1:
                consensus = 1.0
            else:
                largest_group = max(
                    len(v) for v in answers.values()
                )
                consensus = largest_group / n_total

            # Information diversity: higher = more informative
            # Shannon-like: more distinct answers = higher
            if n_distinct <= 1:
                diversity = 0.0
            else:
                diversity = n_distinct / n_total

            results[question] = {
                "n_positions": n_total,
                "n_distinct_answers": n_distinct,
                "consensus_ratio": consensus,
                "diversity_score": diversity,
                "answers": {
                    ans: [p.theory for p in ps]
                    for ans, ps in answers.items()
                },
            }

        return results

    def generate_anomalies(self) -> list[Anomaly]:
        anomalies = []
        analysis = self.analyze()

        for question, data in analysis.items():
            # Only 1 answer across all theories = suspiciously
            # uniform, unless there's genuinely no debate
            if (data["n_positions"] >= 3 and
                    data["n_distinct_answers"] == 1):
                anomalies.append(Anomaly(
                    description=(
                        f"Question '{question}': "
                        f"all {data['n_positions']} sources "
                        f"agree — possible missing dissent"
                    ),
                    gap_type=GapType.VOICE,
                    severity=Severity.MEDIUM,
                    recommendation=(
                        f"Search for scholars who disagree "
                        f"on: {question}"
                    ),
                ))

            # Many positions but only 1 voice per answer =
            # each theory is isolated, no synthesis
            if (data["n_distinct_answers"] >= 3 and
                    all(
                        len(v) == 1
                        for v in data["answers"].values()
                    )):
                anomalies.append(Anomaly(
                    description=(
                        f"Question '{question}': "
                        f"{data['n_distinct_answers']} theories "
                        f"each with single advocate — "
                        f"no synthesis or comparative study"
                    ),
                    gap_type=GapType.VOICE,
                    severity=Severity.MEDIUM,
                    recommendation=(
                        f"Search for comparative or review "
                        f"articles on: {question}"
                    ),
                ))

        return anomalies

    def summary(self) -> str:
        lines = []
        analysis = self.analyze()

        for question, data in analysis.items():
            lines.append(f"Q: {question}")
            lines.append(
                f"  Positions: {data['n_positions']}, "
                f"Distinct answers: "
                f"{data['n_distinct_answers']}, "
                f"Consensus: "
                f"{data['consensus_ratio']:.0%}"
            )
            for ans, theories in data["answers"].items():
                lines.append(
                    f"    \"{ans}\" ← {', '.join(theories)}"
                )

        return "\n".join(lines)


# ============================================================
# PART 3: EMPTY QUERY FEEDBACK
# ============================================================

@dataclass
class QueryResult:
    """The outcome of executing a search query."""
    query: SearchQuery
    n_results: int
    useful_results: int = 0

    @property
    def empty(self) -> bool:
        return self.n_results == 0

    @property
    def low_yield(self) -> bool:
        return 0 < self.n_results <= 1 and self.useful_results == 0


class EmptyQueryAnalyzer:
    """
    Analyzes patterns in query results to extract
    information from absences.
    """

    def __init__(self):
        self.results: list[QueryResult] = []

    def record_result(self, result: QueryResult):
        self.results.append(result)

    def analyze(self) -> dict:
        """
        Analyze patterns in empty vs productive queries.
        Returns insights about where information exists
        and where it doesn't.
        """
        # Group by target entity
        by_entity = defaultdict(list)
        for r in self.results:
            # Extract entity name from query
            entity = r.query.query.split()[0] if r.query.query else ""
            by_entity[entity].append(r)

        # Group by language
        by_language = defaultdict(list)
        for r in self.results:
            by_language[r.query.language].append(r)

        insights = {
            "total_queries": len(self.results),
            "empty_queries": sum(
                1 for r in self.results if r.empty
            ),
            "productive_queries": sum(
                1 for r in self.results if not r.empty
            ),
            "language_productivity": {},
            "entity_reachability": {},
        }

        # Language productivity
        for lang, results in by_language.items():
            productive = sum(1 for r in results if not r.empty)
            total = len(results)
            insights["language_productivity"][lang] = {
                "productive": productive,
                "total": total,
                "ratio": productive / total if total > 0 else 0,
            }

        # Entity reachability: in which languages is each
        # entity findable?
        for entity, results in by_entity.items():
            if not entity:
                continue
            found_in = [
                r.query.language for r in results
                if not r.empty
            ]
            not_found_in = [
                r.query.language for r in results
                if r.empty
            ]
            insights["entity_reachability"][entity] = {
                "found_in": found_in,
                "not_found_in": not_found_in,
            }

        return insights

    def generate_anomalies(self) -> list[Anomaly]:
        anomalies = []
        insights = self.analyze()

        # A language with 0% productivity = we're searching
        # wrong terms in that language
        for lang, data in insights[
            "language_productivity"
        ].items():
            if data["total"] >= 3 and data["ratio"] == 0:
                anomalies.append(Anomaly(
                    description=(
                        f"Language '{lang}': "
                        f"{data['total']} queries, "
                        f"0 results — search terms may "
                        f"need better translation"
                    ),
                    gap_type=GapType.LINGUISTIC,
                    severity=Severity.MEDIUM,
                    recommendation=(
                        f"Review and improve search terms "
                        f"for language '{lang}'"
                    ),
                ))

        # Entity found in some languages but not others =
        # informative asymmetry
        for entity, data in insights[
            "entity_reachability"
        ].items():
            if data["found_in"] and data["not_found_in"]:
                # This is actually normal — but if found
                # ONLY in non-primary languages, flag it
                pass

            # Entity found in NO language = might not exist
            # or might need different search terms
            if (not data["found_in"] and
                    len(data["not_found_in"]) >= 3):
                anomalies.append(Anomaly(
                    description=(
                        f"Entity '{entity}' not found in "
                        f"any language ({len(data['not_found_in'])} "
                        f"tried) — may not have "
                        f"publications, or search terms "
                        f"need revision"
                    ),
                    gap_type=GapType.ENTITY_UNRESEARCHED,
                    severity=Severity.MEDIUM,
                    recommendation=(
                        f"Try alternative spellings or "
                        f"affiliated institution for "
                        f"'{entity}'"
                    ),
                ))

        return anomalies

    def summary(self) -> str:
        insights = self.analyze()
        lines = []
        lines.append(
            f"Queries: {insights['total_queries']} total, "
            f"{insights['productive_queries']} productive, "
            f"{insights['empty_queries']} empty"
        )

        lines.append("Language productivity:")
        for lang, data in sorted(
            insights["language_productivity"].items()
        ):
            lines.append(
                f"  {lang}: {data['productive']}/"
                f"{data['total']} "
                f"({data['ratio']:.0%})"
            )

        reach = insights["entity_reachability"]
        if reach:
            lines.append("Entity reachability:")
            for entity, data in sorted(reach.items()):
                found = ", ".join(data["found_in"]) or "none"
                lines.append(f"  {entity}: found in [{found}]")

        return "\n".join(lines)
