"""Disciplinary expectations — evidence types map to expected disciplines.

When we find certain types of evidence (inscriptions, human remains, mosaics),
we can predict which specialist disciplines should be represented in the
research. Missing disciplines are flagged as anomalies.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from epistemix.models import (
    Anomaly,
    AnomalyType,
    Finding,
    FindingType,
    Postulate,
    PostulateStatus,
    Severity,
)


# Evidence keywords → expected disciplines
EVIDENCE_DISCIPLINE_MAP: dict[str, list[str]] = {
    "inscription": ["epigraphy"],
    "inscriptions": ["epigraphy"],
    "epigraphic": ["epigraphy"],
    "text": ["epigraphy", "philology"],
    "human remains": ["osteology", "physical anthropology"],
    "skeletal": ["osteology", "physical anthropology"],
    "bones": ["osteology"],
    "skeleton": ["osteology"],
    "mosaic": ["art history", "conservation"],
    "mosaics": ["art history", "conservation"],
    "fresco": ["art history", "conservation"],
    "painting": ["art history"],
    "sculpture": ["art history"],
    "pottery": ["ceramics", "typology"],
    "ceramics": ["ceramics", "typology"],
    "coins": ["numismatics"],
    "coin": ["numismatics"],
    "numismatic": ["numismatics"],
    "architecture": ["architectural history"],
    "building": ["architectural history"],
    "tomb": ["funerary archaeology"],
    "burial": ["funerary archaeology", "osteology"],
    "dna": ["archaeogenetics", "molecular biology"],
    "genetic": ["archaeogenetics"],
    "soil": ["geoarchaeology"],
    "sediment": ["geoarchaeology"],
    "geological": ["geoarchaeology", "geology"],
    "radiocarbon": ["chronometry"],
    "dating": ["chronometry"],
    "c14": ["chronometry"],
    "metal": ["archaeometallurgy"],
    "metallurgy": ["archaeometallurgy"],
    "bronze": ["archaeometallurgy"],
    "iron": ["archaeometallurgy"],
    "animal bones": ["zooarchaeology"],
    "fauna": ["zooarchaeology"],
    "plant remains": ["archaeobotany"],
    "seeds": ["archaeobotany"],
    "pollen": ["archaeobotany", "palynology"],
}


@dataclass
class DisciplineExpectations:
    """Track expected disciplines based on evidence types found."""

    # evidence_keyword → set of expected disciplines
    _expected: dict[str, set[str]] = field(default_factory=dict)
    # disciplines confirmed by findings (scholar with matching specialty)
    _confirmed: set[str] = field(default_factory=set)
    # postulates generated for discipline expectations
    _postulates: list[Postulate] = field(default_factory=list)
    _postulate_counter: int = 0

    def register_evidence(self, finding: Finding) -> list[Postulate]:
        """Check if a finding implies expected disciplines and generate postulates."""
        new_postulates = []
        text = f"{finding.name} {finding.description}".lower()

        for keyword, disciplines in EVIDENCE_DISCIPLINE_MAP.items():
            if keyword in text:
                if keyword not in self._expected:
                    self._expected[keyword] = set()
                for disc in disciplines:
                    if disc not in self._expected[keyword]:
                        self._expected[keyword].add(disc)
                        # Generate a postulate for this expected discipline
                        self._postulate_counter += 1
                        p = Postulate(
                            id=f"P-DISC-{self._postulate_counter:03d}",
                            description=(
                                f"A {disc} specialist should be involved in research, "
                                f"given evidence of {keyword}"
                            ),
                            meta_axiom_id="MA-05",
                        )
                        self._postulates.append(p)
                        new_postulates.append(p)

        return new_postulates

    def register_specialist(self, discipline: str) -> None:
        """Mark a discipline as confirmed (a specialist was found)."""
        self._confirmed.add(discipline.lower().strip())

    def confirm_from_finding(self, finding: Finding) -> list[str]:
        """Check if a finding (scholar) matches any expected discipline."""
        confirmed = []
        text = f"{finding.name} {finding.description}".lower()
        all_expected = self.all_expected_disciplines

        for disc in all_expected:
            if disc.lower() in text and disc.lower() not in self._confirmed:
                self._confirmed.add(disc.lower())
                confirmed.append(disc)
                # Confirm matching postulates
                for p in self._postulates:
                    if disc.lower() in p.description.lower() and p.status == PostulateStatus.UNCONFIRMED:
                        p.confirm(finding.name)

        return confirmed

    @property
    def all_expected_disciplines(self) -> set[str]:
        result = set()
        for disciplines in self._expected.values():
            result.update(disciplines)
        return result

    @property
    def missing_disciplines(self) -> set[str]:
        return self.all_expected_disciplines - self._confirmed

    def detect_anomalies(self) -> list[Anomaly]:
        """Flag missing disciplines as anomalies."""
        anomalies = []
        for disc in sorted(self.missing_disciplines):
            # Find which evidence types expect this discipline
            evidence_types = [
                kw for kw, discs in self._expected.items()
                if disc in discs
            ]
            evidence_str = ", ".join(evidence_types)

            severity = Severity.CRITICAL if len(evidence_types) >= 2 else Severity.HIGH

            anomalies.append(Anomaly(
                id=f"A-DISC-{disc.replace(' ', '_')}",
                anomaly_type=AnomalyType.DISCIPLINE_GAP,
                severity=severity,
                description=(
                    f"No {disc} specialist found despite evidence of "
                    f"{evidence_str}"
                ),
                suggested_queries=[
                    f"{disc} specialist research",
                    f"{disc} analysis findings",
                ],
            ))

        return anomalies
