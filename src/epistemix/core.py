"""Core epistemic audit engine — the heart of Epistemix.

Orchestrates postulate generation, query construction, result ingestion,
coverage calculation, anomaly detection, and cycle management.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from epistemix.citation_graph import CitationGraph
from epistemix.connector import BaseConnector, ConnectorResponse, extract_json
from epistemix.content_analysis import ContentAnalysisEngine
from epistemix.disciplines import DisciplineExpectations
from epistemix.meta_axioms import META_AXIOMS, generate_postulate_descriptions
from epistemix.models import (
    Anomaly,
    AnomalyType,
    CoverageScore,
    Finding,
    FindingType,
    Postulate,
    PostulateStatus,
    Query,
    QueryLanguage,
    ResearchState,
    Severity,
)


# ---------------------------------------------------------------------------
# Language support
# ---------------------------------------------------------------------------

COUNTRY_LANGUAGES: dict[str, list[QueryLanguage]] = {
    "greece": [QueryLanguage.GREEK, QueryLanguage.ENGLISH],
    "italy": [QueryLanguage.ITALIAN, QueryLanguage.ENGLISH],
    "france": [QueryLanguage.FRENCH, QueryLanguage.ENGLISH],
    "germany": [QueryLanguage.GERMAN, QueryLanguage.ENGLISH],
    "turkey": [QueryLanguage.TURKISH, QueryLanguage.ENGLISH],
    "egypt": [QueryLanguage.ARABIC, QueryLanguage.ENGLISH],
    "spain": [QueryLanguage.SPANISH, QueryLanguage.ENGLISH],
    "china": [QueryLanguage.CHINESE, QueryLanguage.ENGLISH],
    "japan": [QueryLanguage.JAPANESE, QueryLanguage.ENGLISH],
}

# Pre-built archaeology term translations (extensible per domain)
TERM_TRANSLATIONS: dict[str, dict[QueryLanguage, str]] = {
    "excavation": {
        QueryLanguage.GREEK: "ανασκαφή",
        QueryLanguage.FRENCH: "fouilles",
        QueryLanguage.GERMAN: "Ausgrabung",
        QueryLanguage.ITALIAN: "scavo",
        QueryLanguage.TURKISH: "kazı",
        QueryLanguage.SPANISH: "excavación",
    },
    "tomb": {
        QueryLanguage.GREEK: "τάφος",
        QueryLanguage.FRENCH: "tombeau",
        QueryLanguage.GERMAN: "Grab",
        QueryLanguage.ITALIAN: "tomba",
        QueryLanguage.TURKISH: "mezar",
        QueryLanguage.SPANISH: "tumba",
    },
    "archaeology": {
        QueryLanguage.GREEK: "αρχαιολογία",
        QueryLanguage.FRENCH: "archéologie",
        QueryLanguage.GERMAN: "Archäologie",
        QueryLanguage.ITALIAN: "archeologia",
        QueryLanguage.TURKISH: "arkeoloji",
        QueryLanguage.SPANISH: "arqueología",
    },
    "ancient": {
        QueryLanguage.GREEK: "αρχαίος",
        QueryLanguage.FRENCH: "ancien",
        QueryLanguage.GERMAN: "antik",
        QueryLanguage.ITALIAN: "antico",
        QueryLanguage.TURKISH: "antik",
        QueryLanguage.SPANISH: "antiguo",
    },
    "research": {
        QueryLanguage.GREEK: "έρευνα",
        QueryLanguage.FRENCH: "recherche",
        QueryLanguage.GERMAN: "Forschung",
        QueryLanguage.ITALIAN: "ricerca",
        QueryLanguage.TURKISH: "araştırma",
        QueryLanguage.SPANISH: "investigación",
    },
    "scholar": {
        QueryLanguage.GREEK: "ερευνητής",
        QueryLanguage.FRENCH: "chercheur",
        QueryLanguage.GERMAN: "Forscher",
        QueryLanguage.ITALIAN: "ricercatore",
        QueryLanguage.TURKISH: "araştırmacı",
        QueryLanguage.SPANISH: "investigador",
    },
}


def translate_query(text: str, target_lang: QueryLanguage) -> str:
    """Translate key terms in a query to the target language."""
    if target_lang == QueryLanguage.ENGLISH:
        return text
    result = text.lower()
    for english_term, translations in TERM_TRANSLATIONS.items():
        if target_lang in translations:
            result = result.replace(english_term, translations[target_lang])
    return result


# ---------------------------------------------------------------------------
# Entity extraction from text
# ---------------------------------------------------------------------------

# Patterns for extracting structured entities from text responses
SCHOLAR_PATTERNS = [
    r"(?:Dr\.?|Prof\.?|Professor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:discovered|excavated|studied|published|argued|proposed|suggested|led|directed)",
    r"(?:researcher|archaeologist|scholar|historian|scientist|specialist)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:\((?:\d{4}|et al))",
]

INSTITUTION_PATTERNS = [
    r"((?:University|Institute|Museum|Ministry|Academy|Center|Centre|School|Department)\s+(?:of\s+)?[A-Z][a-zA-Z\s]+?)(?:\.|,|\)|\s{2})",
    r"([A-Z][a-zA-Z]+\s+(?:University|Institute|Museum|Academy))",
    r"(Hellenic\s+Ministry\s+of\s+\w+)",
]

THEORY_PATTERNS = [
    r"(?:theory|hypothesis|interpretation)\s+(?:that|of)\s+(.+?)(?:\.|,|;)",
    r"(.+?)\s+(?:theory|hypothesis)",
]


def extract_entities(text: str, source_query: str = "") -> list[Finding]:
    """Extract named entities from a text response."""
    findings: list[Finding] = []
    seen: set[str] = set()

    # Extract scholars
    for pattern in SCHOLAR_PATTERNS:
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            if len(name) > 5 and name.lower() not in seen:
                seen.add(name.lower())
                findings.append(Finding(
                    name=name,
                    finding_type=FindingType.SCHOLAR,
                    source_query=source_query,
                ))

    # Extract institutions
    for pattern in INSTITUTION_PATTERNS:
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            if len(name) > 5 and name.lower() not in seen:
                seen.add(name.lower())
                findings.append(Finding(
                    name=name,
                    finding_type=FindingType.INSTITUTION,
                    source_query=source_query,
                ))

    # Extract theories
    for pattern in THEORY_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            name = match.group(1).strip()
            if 10 < len(name) < 100 and name.lower() not in seen:
                seen.add(name.lower())
                findings.append(Finding(
                    name=name,
                    finding_type=FindingType.THEORY,
                    source_query=source_query,
                ))

    return findings


# ---------------------------------------------------------------------------
# EpistemicEngine
# ---------------------------------------------------------------------------

@dataclass
class EpistemicEngine:
    """The main epistemic audit engine.

    Orchestrates the full audit cycle:
    1. Initialize postulates from meta-axioms
    2. Generate queries (multilingual)
    3. Execute queries via connector
    4. Ingest results → extract entities → deduplicate
    5. Update postulates based on findings
    6. Detect anomalies
    7. Calculate coverage
    8. Repeat until convergence or max cycles
    """

    connector: BaseConnector
    state: ResearchState
    citation_graph: CitationGraph = field(default_factory=CitationGraph)
    discipline_expectations: DisciplineExpectations = field(
        default_factory=DisciplineExpectations
    )
    content_analysis: ContentAnalysisEngine = field(
        default_factory=ContentAnalysisEngine
    )
    verbose: bool = False

    def initialize_postulates(self) -> list[Postulate]:
        """Generate initial postulates from meta-axioms for this topic/country/discipline."""
        descriptions = generate_postulate_descriptions(
            self.state.topic,
            self.state.country,
            self.state.discipline,
        )
        postulates = []
        for i, (axiom_id, desc) in enumerate(descriptions):
            p = Postulate(
                id=f"P-{axiom_id}-{i:02d}",
                description=desc,
                meta_axiom_id=axiom_id,
                generated_at_cycle=0,
            )
            postulates.append(p)

        self.state.postulates = postulates
        return postulates

    def generate_initial_queries(self) -> list[Query]:
        """Generate multilingual queries for the initial cycle."""
        topic = self.state.topic
        country = self.state.country
        discipline = self.state.discipline

        queries = []

        # English base queries
        base_queries = [
            f"{topic} {country} {discipline} key researchers",
            f"{topic} {country} theories interpretations",
            f"{topic} {country} institutions involved",
            f"{topic} {country} publications review",
            f"{topic} {country} recent discoveries",
        ]

        for text in base_queries:
            queries.append(Query(
                text=text,
                language=QueryLanguage.ENGLISH,
                priority=1.0,
                cycle=self.state.current_cycle,
            ))

        # Add queries in local languages
        country_lower = country.lower()
        if country_lower in COUNTRY_LANGUAGES:
            for lang in COUNTRY_LANGUAGES[country_lower]:
                if lang == QueryLanguage.ENGLISH:
                    continue
                translated = translate_query(
                    f"{topic} {discipline} research {country}", lang
                )
                queries.append(Query(
                    text=translated,
                    language=lang,
                    priority=0.8,
                    cycle=self.state.current_cycle,
                ))

        self.state.queries.extend(queries)
        return queries

    def generate_queries_from_anomalies(self) -> list[Query]:
        """Generate targeted queries from detected anomalies."""
        queries = []
        for anomaly in self.state.unresolved_anomalies:
            for suggested in anomaly.suggested_queries:
                q = Query(
                    text=suggested,
                    language=QueryLanguage.ENGLISH,
                    priority=0.9,
                    source_anomaly_id=anomaly.id,
                    cycle=self.state.current_cycle,
                )
                queries.append(q)

        self.state.queries.extend(queries)
        return queries

    def execute_queries(self, queries: list[Query] | None = None) -> list[ConnectorResponse]:
        """Execute pending queries through the connector."""
        if queries is None:
            queries = [q for q in self.state.queries if not q.executed]

        responses = []
        # Sort by priority (highest first)
        sorted_queries = sorted(queries, key=lambda q: q.priority, reverse=True)

        for query in sorted_queries:
            if query.executed:
                continue
            response = self.connector.search(query.text)
            query.executed = True
            query.result_count = len(response.text) if response.text else 0
            self.content_analysis.register_query(query)
            responses.append(response)

        return responses

    def ingest_results(self, responses: list[ConnectorResponse]) -> list[Finding]:
        """Extract entities from responses and add to state."""
        new_findings: list[Finding] = []

        for response in responses:
            entities = extract_entities(response.text)
            for entity in entities:
                if self.state.add_finding(entity):
                    new_findings.append(entity)
                    # Register in subsystems
                    self.citation_graph.add_finding(entity)
                    self.content_analysis.register_finding(entity)

                    # Register evidence for discipline expectations
                    if entity.finding_type == FindingType.EVIDENCE:
                        new_postulates = self.discipline_expectations.register_evidence(entity)
                        self.state.postulates.extend(new_postulates)

                    # Try to confirm discipline expectations from scholars
                    if entity.finding_type == FindingType.SCHOLAR:
                        self.discipline_expectations.confirm_from_finding(entity)

        return new_findings

    def update_postulates(self, new_findings: list[Finding]) -> None:
        """Update postulate statuses based on new findings."""
        for postulate in self.state.postulates:
            if postulate.status == PostulateStatus.CONFIRMED:
                continue
            self._try_confirm_postulate(postulate, new_findings)

    def _try_confirm_postulate(
        self, postulate: Postulate, findings: list[Finding]
    ) -> None:
        """Try to confirm a postulate based on available findings."""
        desc_lower = postulate.description.lower()

        for finding in findings:
            finding_text = f"{finding.name} {finding.description}".lower()

            # Language postulates
            if postulate.meta_axiom_id == "MA-01":
                if "local language" in desc_lower or "non-english" in desc_lower:
                    if finding.language != QueryLanguage.ENGLISH:
                        postulate.confirm(finding.name)
                        return
                if "terminology" in desc_lower and finding.finding_type == FindingType.OTHER:
                    postulate.confirm(finding.name)
                    return

            # Institution postulates
            elif postulate.meta_axiom_id == "MA-02":
                if finding.finding_type == FindingType.INSTITUTION:
                    if "university" in desc_lower and "university" in finding_text:
                        postulate.confirm(finding.name)
                        return
                    if "government" in desc_lower and any(
                        w in finding_text for w in ["ministry", "government", "state"]
                    ):
                        postulate.confirm(finding.name)
                        return
                    if "international" in desc_lower:
                        postulate.confirm(finding.name)
                        return

            # Theory postulates
            elif postulate.meta_axiom_id == "MA-03":
                if finding.finding_type == FindingType.THEORY:
                    theories = [
                        f for f in self.state.findings
                        if f.finding_type == FindingType.THEORY
                    ]
                    if len(set(theories)) >= 2:
                        postulate.confirm(finding.name)
                        return

            # School postulates
            elif postulate.meta_axiom_id == "MA-04":
                schools = self.citation_graph.detect_schools()
                if len(schools) >= 2:
                    postulate.confirm(finding.name)
                    return
                if finding.finding_type == FindingType.SCHOOL:
                    postulate.confirm(finding.name)
                    return

            # Discipline postulates
            elif postulate.meta_axiom_id == "MA-05":
                if finding.finding_type in (FindingType.METHOD, FindingType.EVIDENCE):
                    disciplines_found = len(
                        self.discipline_expectations.all_expected_disciplines
                    )
                    if disciplines_found >= 2:
                        postulate.confirm(finding.name)
                        return

            # Publication postulates
            elif postulate.meta_axiom_id == "MA-06":
                if finding.finding_type == FindingType.PUBLICATION:
                    postulate.confirm(finding.name)
                    return
                # Check if any publication-related terms in findings
                if any(w in finding_text for w in [
                    "journal", "proceedings", "publication", "published",
                    "thesis", "report", "book",
                ]):
                    postulate.confirm(finding.name)
                    return

            # Temporal postulates
            elif postulate.meta_axiom_id == "MA-07":
                if "span" in desc_lower or "decades" in desc_lower:
                    # Check if we have findings from different eras
                    if any(w in finding_text for w in [
                        "1960", "1970", "1980", "1990", "2000", "2010",
                        "earlier", "pioneer", "historical", "early",
                    ]):
                        postulate.confirm(finding.name)
                        return
                if "earlier interpretations" in desc_lower:
                    if any(w in finding_text for w in [
                        "revised", "reinterpreted", "previously",
                        "earlier", "original", "initial",
                    ]):
                        postulate.confirm(finding.name)
                        return

    def detect_anomalies(self) -> list[Anomaly]:
        """Run all anomaly detectors and collect results."""
        new_anomalies: list[Anomaly] = []

        # Citation graph anomalies
        cg_anomalies = self.citation_graph.generate_anomalies()
        for a in cg_anomalies:
            a.detected_at_cycle = self.state.current_cycle
            if self.state.add_anomaly(a):
                new_anomalies.append(a)

        # Discipline gap anomalies
        disc_anomalies = self.discipline_expectations.detect_anomalies()
        for a in disc_anomalies:
            a.detected_at_cycle = self.state.current_cycle
            if self.state.add_anomaly(a):
                new_anomalies.append(a)

        # Content analysis anomalies
        ca_anomalies = self.content_analysis.detect_all_anomalies()
        for a in ca_anomalies:
            a.detected_at_cycle = self.state.current_cycle
            if self.state.add_anomaly(a):
                new_anomalies.append(a)

        # Language gap check
        lang_anomaly = self._check_language_gaps()
        if lang_anomaly:
            lang_anomaly.detected_at_cycle = self.state.current_cycle
            if self.state.add_anomaly(lang_anomaly):
                new_anomalies.append(lang_anomaly)

        return new_anomalies

    def _check_language_gaps(self) -> Anomaly | None:
        """Check if we're missing findings in expected languages."""
        country_lower = self.state.country.lower()
        expected_langs = COUNTRY_LANGUAGES.get(country_lower, [])

        if not expected_langs:
            return None

        found_langs = {f.language for f in self.state.findings}
        non_english_expected = [
            l for l in expected_langs if l != QueryLanguage.ENGLISH
        ]

        for lang in non_english_expected:
            if lang not in found_langs:
                return Anomaly(
                    id=f"A-LANG-{lang.value}",
                    anomaly_type=AnomalyType.LANGUAGE_GAP,
                    severity=Severity.HIGH,
                    description=(
                        f"No {lang.name}-language sources found for research in "
                        f"{self.state.country}"
                    ),
                    suggested_queries=[
                        translate_query(
                            f"{self.state.topic} {self.state.discipline} research",
                            lang,
                        )
                    ],
                )

        return None

    def calculate_coverage(self) -> CoverageScore:
        """Calculate current coverage score."""
        coverage = self.state.current_coverage()
        coverage.cycle = self.state.current_cycle
        self.state.coverage_history.append(coverage)
        return coverage

    def run_cycle(self, cycle: int | None = None) -> CoverageScore:
        """Run a single audit cycle."""
        if cycle is not None:
            self.state.current_cycle = cycle

        if self.state.current_cycle == 0:
            # First cycle: initialize everything
            if not self.state.postulates:
                self.initialize_postulates()
            queries = self.generate_initial_queries()
        else:
            # Subsequent cycles: generate queries from anomalies
            queries = self.generate_queries_from_anomalies()
            if not queries:
                # If no anomaly-driven queries, generate broader queries
                queries = self._generate_broadening_queries()

        # Execute queries
        responses = self.execute_queries(queries)

        # Ingest results
        new_findings = self.ingest_results(responses)

        # Update postulates
        self.update_postulates(new_findings)

        # Detect anomalies
        self.detect_anomalies()

        # Calculate coverage
        coverage = self.calculate_coverage()

        if self.verbose:
            print(
                f"Cycle {self.state.current_cycle}: "
                f"{len(new_findings)} new findings, "
                f"coverage={coverage.percentage}%, "
                f"anomalies={coverage.anomaly_count}"
            )

        return coverage

    def _generate_broadening_queries(self) -> list[Query]:
        """Generate broader queries when anomaly-driven ones are exhausted."""
        topic = self.state.topic
        country = self.state.country
        cycle = self.state.current_cycle

        templates = [
            f"{topic} {country} criticism debate controversy",
            f"{topic} {country} alternative interpretations",
            f"{topic} {country} overlooked aspects",
            f"{topic} {country} interdisciplinary studies",
        ]

        queries = []
        for text in templates[:2]:  # Limit to 2 per cycle
            queries.append(Query(
                text=text,
                language=QueryLanguage.ENGLISH,
                priority=0.7,
                cycle=cycle,
            ))

        self.state.queries.extend(queries)
        return queries

    def run_all_cycles(
        self, max_cycles: int = 4, convergence_threshold: float = 2.0
    ) -> list[CoverageScore]:
        """Run all cycles until convergence or max cycles reached.

        Convergence: coverage increase < threshold between cycles.
        """
        all_coverage: list[CoverageScore] = []

        for cycle in range(max_cycles):
            coverage = self.run_cycle(cycle)
            all_coverage.append(coverage)

            # Check convergence after at least 2 cycles
            if cycle >= 2 and len(all_coverage) >= 2:
                prev = all_coverage[-2].percentage
                curr = coverage.percentage
                if curr - prev < convergence_threshold:
                    if self.verbose:
                        print(
                            f"Convergence reached at cycle {cycle}: "
                            f"{curr - prev:.1f}% improvement < {convergence_threshold}%"
                        )
                    break

            self.state.current_cycle += 1

        return all_coverage
