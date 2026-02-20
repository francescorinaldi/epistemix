"""Disciplinary expectations — evidence types map to expected specialist disciplines.

Based on the founder's v2 design with:
  - SubDiscipline templates with relevance vs specialist keywords
  - Pre-built discipline sets (archaeology, etc.)
  - DisciplineAnalyzer that builds text corpus from findings

When evidence types are found (inscriptions, bones, mosaics, coins),
the system predicts which specialist disciplines should be represented.
Missing specialists are flagged as anomalies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from epistemix.models import Anomaly, Expectation, Finding, GapType, Severity


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class SubDiscipline:
    """A specialist sub-discipline with detection keywords."""
    name: str
    keywords: list[str] = field(default_factory=list)
    specialist_keywords: list[str] = field(default_factory=list)
    required: bool = False
    relevance_reason: str = ""


# ============================================================
# DISCIPLINE TEMPLATES
# ============================================================

ARCHAEOLOGY_DISCIPLINES: list[SubDiscipline] = [
    SubDiscipline(
        name="Field archaeology",
        keywords=["excavation", "stratigraphy", "trench", "survey", "dig"],
        specialist_keywords=["archaeologist", "excavator", "field director"],
        required=True,
        relevance_reason="Core discipline for any excavation",
    ),
    SubDiscipline(
        name="Epigraphy",
        keywords=["inscription", "epigraph", "text", "graffiti", "letter", "monogram"],
        specialist_keywords=["epigraphist", "epigrapher", "philologist"],
        relevance_reason="Inscriptions require specialist reading",
    ),
    SubDiscipline(
        name="Osteology",
        keywords=["bone", "skeleton", "remains", "burial", "human remains", "individual"],
        specialist_keywords=["osteologist", "bioarchaeologist", "anthropologist"],
        relevance_reason="Human remains require specialist analysis",
    ),
    SubDiscipline(
        name="Ancient history",
        keywords=["ancient", "historical", "source", "text", "literary", "account"],
        specialist_keywords=["historian", "classicist", "ancient historian"],
        required=True,
        relevance_reason="Historical context for any archaeological site",
    ),
    SubDiscipline(
        name="Archaeoastronomy",
        keywords=["alignment", "solstice", "equinox", "orientation", "astronomical"],
        specialist_keywords=["archaeoastronomer", "astronomer"],
        relevance_reason="Astronomical alignments require specialist verification",
    ),
    SubDiscipline(
        name="Art history",
        keywords=["mosaic", "painting", "sculpture", "relief", "fresco", "caryatid", "sphinx"],
        specialist_keywords=["art historian", "iconographer"],
        relevance_reason="Artistic elements require specialist interpretation",
    ),
    SubDiscipline(
        name="Architecture",
        keywords=["architecture", "building", "structure", "vault", "column", "chamber", "wall"],
        specialist_keywords=["architect", "architectural historian"],
        relevance_reason="Structural analysis requires specialist knowledge",
    ),
    SubDiscipline(
        name="DNA analysis",
        keywords=["dna", "genetic", "genome", "mitochondrial", "adna", "ancient dna"],
        specialist_keywords=["geneticist", "paleogeneticist", "molecular biologist"],
        relevance_reason="Genetic analysis requires specialist lab work",
    ),
    SubDiscipline(
        name="Numismatics",
        keywords=["coin", "numismatic", "currency", "mint", "coinage"],
        specialist_keywords=["numismatist"],
        relevance_reason="Coins require specialist dating and identification",
    ),
    SubDiscipline(
        name="Ceramics",
        keywords=["pottery", "ceramic", "vessel", "amphora", "sherd", "fragment"],
        specialist_keywords=["ceramicist", "pottery specialist"],
        relevance_reason="Pottery is key dating evidence",
    ),
]


def get_discipline_set(discipline: str) -> list[SubDiscipline]:
    """Get the appropriate discipline template set."""
    discipline_lower = discipline.lower()
    if discipline_lower in ("archaeology", "archeology"):
        return ARCHAEOLOGY_DISCIPLINES
    # Default: return archaeology (most developed template)
    # Future: add biology, medicine, history, etc.
    return ARCHAEOLOGY_DISCIPLINES


# ============================================================
# DISCIPLINE ANALYZER
# ============================================================

class DisciplineAnalyzer:
    """Analyzes findings for disciplinary coverage.

    Builds a text corpus from all findings, then checks which
    sub-disciplines are relevant (keyword match) and which
    specialists have been found.
    """

    def __init__(self, discipline: str = "archaeology") -> None:
        self.disciplines = get_discipline_set(discipline)
        self.findings: list[Finding] = []
        self._corpus: str = ""
        self._relevant: dict[str, bool] = {}
        self._specialist_found: dict[str, bool] = {}

    def ingest_findings(self, findings: list[Finding]) -> None:
        """Build text corpus from findings."""
        self.findings = findings
        # Build corpus from all text fields
        parts: list[str] = []
        for f in findings:
            parts.append(f.source.lower())
            if f.author:
                parts.append(f.author.lower())
            if f.institution:
                parts.append(f.institution.lower())
            if f.theory_supported:
                parts.append(f.theory_supported.lower())
            for entity in f.entities_mentioned:
                parts.append(entity.lower())
        self._corpus = " ".join(parts)
        self._analyze()

    def _analyze(self) -> None:
        """Check relevance and specialist presence for each discipline."""
        for disc in self.disciplines:
            # Check if evidence keywords are present
            self._relevant[disc.name] = (
                disc.required
                or any(kw in self._corpus for kw in disc.keywords)
            )

            # Check if specialist keywords are present
            self._specialist_found[disc.name] = any(
                kw in self._corpus for kw in disc.specialist_keywords
            )

    def generate_expectations(self, cycle: int = 0) -> list[Expectation]:
        """Generate expectations for relevant disciplines."""
        expectations: list[Expectation] = []
        for disc in self.disciplines:
            if self._relevant.get(disc.name, False):
                expectations.append(Expectation(
                    description=(
                        f"Specialist in {disc.name} found or referenced"
                    ),
                    gap_type=GapType.DISCIPLINE_GAP,
                    severity_if_unmet=(
                        Severity.HIGH if disc.required
                        else Severity.MEDIUM
                    ),
                    met=self._specialist_found.get(disc.name, False),
                    evidence=(
                        f"Specialist keywords found in corpus"
                        if self._specialist_found.get(disc.name)
                        else ""
                    ),
                    derived_in_cycle=cycle,
                ))
        return expectations

    def generate_anomalies(self) -> list[Anomaly]:
        """Generate anomalies for missing specialists."""
        anomalies: list[Anomaly] = []

        for disc in self.disciplines:
            if (
                self._relevant.get(disc.name, False)
                and not self._specialist_found.get(disc.name, False)
            ):
                # Count how many evidence keywords match
                keyword_count = sum(
                    1 for kw in disc.keywords if kw in self._corpus
                )
                severity = (
                    Severity.CRITICAL if keyword_count >= 3 or disc.required
                    else Severity.HIGH if keyword_count >= 2
                    else Severity.MEDIUM
                )

                anomalies.append(Anomaly(
                    description=(
                        f"No {disc.name} specialist found despite "
                        f"evidence ({disc.relevance_reason})"
                    ),
                    gap_type=GapType.DISCIPLINE_GAP,
                    severity=severity,
                    recommendation=(
                        f"Search for {disc.name} specialists working on "
                        f"this topic"
                    ),
                    suggested_queries=[
                        f"{disc.name} specialist research",
                        f"{disc.specialist_keywords[0]} {disc.keywords[0]} analysis"
                        if disc.specialist_keywords and disc.keywords
                        else f"{disc.name} analysis",
                    ],
                ))

        return anomalies

    def coverage_summary(self) -> dict[str, Any]:
        """Summary of disciplinary coverage."""
        relevant = [
            d.name for d in self.disciplines
            if self._relevant.get(d.name, False)
        ]
        covered = [
            d.name for d in self.disciplines
            if self._relevant.get(d.name, False)
            and self._specialist_found.get(d.name, False)
        ]
        missing = [
            d.name for d in self.disciplines
            if self._relevant.get(d.name, False)
            and not self._specialist_found.get(d.name, False)
        ]
        return {
            "relevant_disciplines": relevant,
            "covered": covered,
            "missing": missing,
            "coverage_ratio": (
                len(covered) / len(relevant) if relevant else 0
            ),
        }
