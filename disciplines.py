"""
EPISTEMIX v2 — Disciplinary Expectations Module

Each research domain involves multiple sub-disciplines.
Each sub-discipline has its own specialist community.
If a sub-discipline is relevant to the topic but no
specialist voice has been found, that's a gap.

Example for Amphipolis:
  - Hellenistic archaeology → excavator (Peristeri) ✓
  - Ancient history → historian (Mavrogiannis, Chugg) ✓
  - Archaeoastronomy → specialist (Savvides) ✓
  - Epigraphy → specialist (???) ✗
  - Osteology/forensic anthropology → specialist (???) ✗
  - Conservation/restoration → specialist (???) ✗

The module doesn't hardcode which scholar fills which
role — it infers from keywords in findings and theories.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from core import (
    Finding, DynamicPostulates, Expectation,
    Anomaly, Severity, GapType
)


@dataclass
class SubDiscipline:
    """A sub-discipline relevant to a research domain."""
    name: str
    keywords: list[str]          # Terms that indicate relevance
    specialist_keywords: list[str]  # Terms indicating a specialist
    required: bool = True        # Always expected, or conditional?
    relevance_reason: str = ""   # Why this discipline matters here

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, SubDiscipline):
            return self.name == other.name
        return False


@dataclass
class DisciplinaryCoverage:
    """Tracks coverage of a sub-discipline."""
    discipline: SubDiscipline
    relevant: bool = False       # Is it relevant to this topic?
    relevance_evidence: str = ""
    specialist_found: bool = False
    specialist_name: str = ""
    specialist_evidence: str = ""


# ============================================================
# DISCIPLINE TEMPLATES
# ============================================================

# Templates for common research domains
ARCHAEOLOGY_DISCIPLINES = [
    SubDiscipline(
        name="Field archaeology / Excavation",
        keywords=[
            "excavation", "excavator", "dig", "stratigraphy",
            "trench", "ανασκαφή", "scavo",
        ],
        specialist_keywords=[
            "excavat", "field director", "dig director",
            "site director", "ανασκαφ", "scav",
        ],
        required=True,
        relevance_reason="Every excavation has a lead archaeologist",
    ),
    SubDiscipline(
        name="Epigraphy",
        keywords=[
            "inscription", "epigraph", "letters", "text",
            "graffiti", "ΠΑΡΕΛΑΒΟΝ", "monogram",
            "iscrizione", "Inschrift",
        ],
        specialist_keywords=[
            "epigraph", "epigrapher", "iscrizi",
        ],
        relevance_reason=(
            "If inscriptions are found, an epigraphist "
            "should have examined them"
        ),
    ),
    SubDiscipline(
        name="Osteology / Physical anthropology",
        keywords=[
            "bones", "skeleton", "skeletal", "remains",
            "burial", "cremation", "cremated", "newborn",
            "osteolog", "anthropolog",
        ],
        specialist_keywords=[
            "osteolog", "anthropolog", "forensic",
            "bioarchaeolog",
        ],
        relevance_reason=(
            "If human remains are found, an osteologist "
            "should have analyzed them"
        ),
    ),
    SubDiscipline(
        name="Ancient history",
        keywords=[
            "historical", "ancient source", "diodorus",
            "plutarch", "arrian", "literary",
            "chronolog", "dynasty",
        ],
        specialist_keywords=[
            "historian", "history professor",
            "ancient history", "historical analysis",
        ],
        relevance_reason="Historical context requires specialists",
    ),
    SubDiscipline(
        name="Archaeoastronomy",
        keywords=[
            "solar", "solstice", "equinox", "alignment",
            "astronomical", "celestial", "orientation",
            "sunrise", "sunset",
        ],
        specialist_keywords=[
            "archaeoastronom", "solar alignment",
            "astronomical",
        ],
        relevance_reason=(
            "If astronomical alignments are claimed, "
            "an archaeoastronomer should verify"
        ),
    ),
    SubDiscipline(
        name="Art history / Iconography",
        keywords=[
            "mosaic", "fresco", "painting", "sculpture",
            "sphinx", "caryatid", "lion", "Persephone",
            "iconograph", "style",
        ],
        specialist_keywords=[
            "art hist", "iconograph", "mosaic specialist",
        ],
        relevance_reason=(
            "Decorative elements require art historical "
            "interpretation"
        ),
    ),
    SubDiscipline(
        name="Architecture / Engineering",
        keywords=[
            "architecture", "construction", "structure",
            "vault", "wall", "marble", "limestone",
            "tumulus", "monument", "diameter", "height",
        ],
        specialist_keywords=[
            "architect", "engineer", "structural",
            "conservation",
        ],
        relevance_reason="Monumental architecture needs specialists",
    ),
    SubDiscipline(
        name="DNA analysis / Genetics",
        keywords=[
            "DNA", "genetic", "genome", "mitochondrial",
            "ancient DNA", "aDNA",
        ],
        specialist_keywords=[
            "genetic", "DNA", "genomic", "paleogenet",
        ],
        relevance_reason=(
            "If remains exist, DNA analysis may be "
            "attempted or expected"
        ),
    ),
    SubDiscipline(
        name="Numismatics",
        keywords=[
            "coin", "coins", "numismat", "mint",
            "currency", "drachma",
        ],
        specialist_keywords=["numismat"],
        required=False,
        relevance_reason="Relevant only if coins are found",
    ),
    SubDiscipline(
        name="Ceramics / Pottery analysis",
        keywords=[
            "pottery", "ceramic", "vessel", "amphora",
            "sherd", "fragment",
        ],
        specialist_keywords=["ceramolog", "pottery specialist"],
        required=False,
        relevance_reason="Relevant only if ceramics are found",
    ),
]


# ============================================================
# DISCIPLINE ANALYZER
# ============================================================

class DisciplineAnalyzer:
    """
    Analyzes findings to determine which sub-disciplines
    are relevant and whether specialists have been found.
    """

    def __init__(
        self,
        discipline_templates: list[SubDiscipline] | None = None
    ):
        self.templates = (
            discipline_templates or ARCHAEOLOGY_DISCIPLINES
        )
        self.coverage: list[DisciplinaryCoverage] = []

    def analyze(
        self,
        findings: list[Finding],
        postulates: DynamicPostulates,
    ) -> list[DisciplinaryCoverage]:
        """
        Scan findings to determine relevance and coverage
        of each sub-discipline.
        """
        self.coverage = []

        # Build a text corpus from all findings
        corpus = self._build_corpus(findings)

        for disc in self.templates:
            cov = DisciplinaryCoverage(discipline=disc)

            # Check relevance: do any keywords appear?
            for kw in disc.keywords:
                if kw.lower() in corpus:
                    cov.relevant = True
                    cov.relevance_evidence = (
                        f"Keyword '{kw}' found in findings"
                    )
                    break

            # Check specialist: is there an author whose
            # findings contain specialist keywords?
            if cov.relevant:
                cov.specialist_found, cov.specialist_name, \
                    cov.specialist_evidence = (
                        self._find_specialist(findings, disc)
                    )

            self.coverage.append(cov)

        return self.coverage

    def _build_corpus(self, findings: list[Finding]) -> str:
        """Concatenate all finding text into searchable corpus."""
        parts = []
        for f in findings:
            parts.append(f.source.lower())
            parts.append(f.theory_supported.lower())
            for e in f.entities_mentioned:
                parts.append(e.lower())
        return " ".join(parts)

    def _find_specialist(
        self, findings: list[Finding], disc: SubDiscipline
    ) -> tuple[bool, str, str]:
        """
        Check if any finding's author appears to be a
        specialist in this sub-discipline.
        """
        for f in findings:
            if not f.author:
                continue

            # Check source, theory, and mentioned entities
            finding_text = (
                f.source.lower() + " " +
                f.theory_supported.lower() + " " +
                " ".join(e.lower() for e in f.entities_mentioned)
            )

            for kw in disc.specialist_keywords:
                if kw.lower() in finding_text:
                    return (
                        True,
                        f.author,
                        f"'{kw}' in {f.source}"
                    )

        return False, "", ""

    def generate_expectations(
        self, cycle: int
    ) -> list[Expectation]:
        """Generate expectations from disciplinary analysis."""
        expectations = []

        for cov in self.coverage:
            if cov.relevant:
                expectations.append(Expectation(
                    description=(
                        f"Specialist in "
                        f"'{cov.discipline.name}' identified "
                        f"(relevance: {cov.relevance_evidence})"
                    ),
                    gap_type=GapType.VOICE,
                    severity_if_unmet=Severity.HIGH,
                    met=cov.specialist_found,
                    evidence=(
                        cov.specialist_evidence
                        if cov.specialist_found else ""
                    ),
                    derived_in_cycle=cycle,
                ))

        return expectations

    def generate_anomalies(self) -> list[Anomaly]:
        """Generate anomalies for missing specialists."""
        anomalies = []

        for cov in self.coverage:
            if cov.relevant and not cov.specialist_found:
                anomalies.append(Anomaly(
                    description=(
                        f"No specialist in "
                        f"'{cov.discipline.name}' found, "
                        f"but discipline is relevant: "
                        f"{cov.relevance_evidence}"
                    ),
                    gap_type=GapType.VOICE,
                    severity=Severity.HIGH,
                    recommendation=(
                        f"Search for "
                        f"{cov.discipline.name} specialist "
                        f"who has worked on this topic"
                    ),
                ))

        return anomalies

    def summary(self) -> str:
        """Human-readable summary."""
        lines = []
        relevant = [c for c in self.coverage if c.relevant]
        lines.append(
            f"Sub-disciplines relevant: "
            f"{len(relevant)}/{len(self.coverage)}"
        )

        for cov in self.coverage:
            if cov.relevant:
                if cov.specialist_found:
                    status = f"✓ {cov.specialist_name}"
                else:
                    status = "✗ NO SPECIALIST FOUND"
                lines.append(
                    f"  {cov.discipline.name}: {status}"
                )
            else:
                lines.append(
                    f"  {cov.discipline.name}: (not relevant)"
                )

        return "\n".join(lines)
