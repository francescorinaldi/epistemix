"""Level 0 meta-axioms — fixed structural knowledge about how research works.

These are domain-independent truths about academic research that hold
regardless of topic, country, or discipline. They drive the initial
postulate generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MetaAxiom:
    """A structural axiom about research."""
    id: str
    name: str
    description: str
    postulate_templates: tuple[str, ...] = field(default_factory=tuple)


# The 7 Level 0 meta-axioms

MA_01_LANGUAGE = MetaAxiom(
    id="MA-01",
    name="Linguistic Diversity",
    description=(
        "Significant research on any topic exists in multiple languages. "
        "A monolingual search inherently misses perspectives."
    ),
    postulate_templates=(
        "Research on {topic} in {country} exists in the local language(s)",
        "At least one non-English publication on {topic} in {country} exists",
        "Key terminology for {topic} differs across languages",
    ),
)

MA_02_INSTITUTION = MetaAxiom(
    id="MA-02",
    name="Institutional Multiplicity",
    description=(
        "Research involves multiple institutions — universities, museums, "
        "government agencies, NGOs. No single institution holds all knowledge."
    ),
    postulate_templates=(
        "At least one university has studied {topic} in {country}",
        "A government or cultural institution is involved in {topic} in {country}",
        "International collaboration exists on {topic} in {country}",
    ),
)

MA_03_THEORY = MetaAxiom(
    id="MA-03",
    name="Theoretical Pluralism",
    description=(
        "Mature research areas have competing theoretical frameworks. "
        "A single theory indicates either a new field or an echo chamber."
    ),
    postulate_templates=(
        "At least two competing interpretations of {topic} in {country} exist",
        "A theoretical debate about {topic} in {country} has been published",
    ),
)

MA_04_SCHOOL = MetaAxiom(
    id="MA-04",
    name="School Formation",
    description=(
        "Researchers cluster into citation networks (schools). "
        "A single school suggests blind spots in the search."
    ),
    postulate_templates=(
        "At least two distinct research groups study {topic} in {country}",
        "Citation patterns reveal distinct communities",
    ),
)

MA_05_DISCIPLINE = MetaAxiom(
    id="MA-05",
    name="Disciplinary Breadth",
    description=(
        "Complex topics require input from multiple disciplines. "
        "Missing disciplines indicate unexplored angles."
    ),
    postulate_templates=(
        "Multiple academic disciplines have contributed to understanding {topic} in {country}",
        "Interdisciplinary work on {topic} in {country} exists",
    ),
)

MA_06_PUBLICATION = MetaAxiom(
    id="MA-06",
    name="Publication Channels",
    description=(
        "Research is disseminated through multiple channels — journals, "
        "conferences, books, grey literature. Missing channels mean missing data."
    ),
    postulate_templates=(
        "Peer-reviewed publications on {topic} in {country} exist",
        "Conference proceedings or reports on {topic} in {country} exist",
        "Grey literature (theses, technical reports) on {topic} in {country} exists",
    ),
)

MA_07_TEMPORAL = MetaAxiom(
    id="MA-07",
    name="Temporal Evolution",
    description=(
        "Understanding of any topic evolves over time. The current consensus "
        "differs from earlier interpretations, and tracing this evolution "
        "reveals what was considered and abandoned."
    ),
    postulate_templates=(
        "Research on {topic} in {country} spans multiple decades",
        "Earlier interpretations of {topic} in {country} differ from current ones",
    ),
)


META_AXIOMS: tuple[MetaAxiom, ...] = (
    MA_01_LANGUAGE,
    MA_02_INSTITUTION,
    MA_03_THEORY,
    MA_04_SCHOOL,
    MA_05_DISCIPLINE,
    MA_06_PUBLICATION,
    MA_07_TEMPORAL,
)

META_AXIOM_BY_ID: dict[str, MetaAxiom] = {ma.id: ma for ma in META_AXIOMS}


def generate_postulate_descriptions(
    topic: str, country: str, discipline: str
) -> list[tuple[str, str]]:
    """Generate (meta_axiom_id, postulate_description) pairs from all axioms."""
    results = []
    context = {"topic": topic, "country": country, "discipline": discipline}
    for axiom in META_AXIOMS:
        for template in axiom.postulate_templates:
            description = template.format(**context)
            results.append((axiom.id, description))
    return results
