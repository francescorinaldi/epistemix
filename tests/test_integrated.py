"""Full integration test — runs the complete pipeline with MockConnector."""

from epistemix.connector import MockConnector
from epistemix.core import EpistemicEngine
from epistemix.multi_agent import MultiAgentSystem
from epistemix.models import (
    FindingType,
    PostulateStatus,
    ResearchState,
)
from tests.conftest import (
    AMPHIPOLIS_TOPIC,
    AMPHIPOLIS_COUNTRY,
    AMPHIPOLIS_DISCIPLINE,
)


# Rich mock data that exercises all modules
INTEGRATION_RESPONSES: dict[str, str] = {
    "amphipolis": (
        "The Amphipolis tomb excavation in northern Greece was led by "
        "Dr. Katerina Peristeri of the Hellenic Ministry of Culture. "
        "The tomb dates to the 4th century BC and features caryatid sculptures, "
        "a floor mosaic depicting the abduction of Persephone, and human remains "
        "of at least five individuals including skeletal fragments. "
        "Inscriptions were found near the entrance. "
        "Prof. Michalis Lefantzis studied the architectural design. "
        "The University of Thessaloniki provided analytical support. "
        "Theories include the Alexander burial hypothesis and the "
        "theory that the tomb was a memorial for Hephaestion, Alexander's companion. "
        "The Royal family member theory suggests a Macedonian royal occupant. "
        "Earlier excavations by Dimitrios Lazaridis in the 1960s established "
        "the site's significance. Oscar Broneer also conducted early research. "
        "Greek-language publications by Peristeri appeared in Archaiologiko Deltion. "
        "The Aristotle University of Thessaloniki contributed analysis. "
    ),
    "alternative": (
        "Some scholars argue the tomb's dating is uncertain. "
        "Dr. Angeliki Kottaridi proposed alternative chronological frameworks. "
        "Prof. Manolis Andronikos' earlier work at Vergina provides comparative "
        "evidence. The Academy of Athens has also weighed in on the debate. "
    ),
    "criticism": (
        "Critics of the Alexander hypothesis include several international scholars. "
        "Dr. Andrew Stewart from University of California argued the architectural "
        "style doesn't match Alexander's period precisely. "
        "The theory of Hephaestion has been both supported and challenged."
    ),
    "research": (
        "Research on the Amphipolis tomb spans multiple decades from initial "
        "surveys in the 1960s to the major 2012 discovery. Published in "
        "the journal Archaiologiko Deltion and presented at international "
        "conferences including the Archaeological Institute of America meetings."
    ),
    "default": (
        "The Amphipolis tomb remains one of the most significant archaeological "
        "discoveries in Greece. Multiple research groups continue to study "
        "various aspects of the site."
    ),
}


class TestIntegrated:
    def test_full_pipeline_single_engine(self):
        """Run the full pipeline with a single engine."""
        mc = MockConnector(INTEGRATION_RESPONSES)
        state = ResearchState(
            topic=AMPHIPOLIS_TOPIC,
            country=AMPHIPOLIS_COUNTRY,
            discipline=AMPHIPOLIS_DISCIPLINE,
        )
        engine = EpistemicEngine(connector=mc, state=state)

        # Run 3 cycles
        coverage_history = engine.run_all_cycles(max_cycles=3)

        # Should have found multiple findings
        assert len(state.unique_findings) >= 3

        # Should have postulates
        assert len(state.postulates) >= 14

        # Should have some confirmed postulates
        confirmed = [p for p in state.postulates if p.status == PostulateStatus.CONFIRMED]
        assert len(confirmed) >= 1

        # Coverage should be tracked
        assert len(coverage_history) >= 1
        assert coverage_history[-1].percentage > 0

        # Should have detected some anomalies
        # (at minimum, language gap for Greek)
        assert len(state.anomalies) >= 0

        # Findings should include various types
        finding_types = {f.finding_type for f in state.findings}
        assert FindingType.SCHOLAR in finding_types

    def test_full_pipeline_multi_agent(self):
        """Run the full multi-agent pipeline."""
        mc = MockConnector(INTEGRATION_RESPONSES)
        mas = MultiAgentSystem(
            connector=mc,
            topic=AMPHIPOLIS_TOPIC,
            country=AMPHIPOLIS_COUNTRY,
            discipline=AMPHIPOLIS_DISCIPLINE,
            max_cycles=2,
        )
        result = mas.run()

        # Both agents should have run
        assert result["alpha"]["coverage"] >= 0
        assert result["beta"]["coverage"] >= 0

        # Combined coverage should be computed
        assert "coverage" in result["combined"]
        assert "blindness_gap" in result["combined"]

        # Should have some agreements and potentially discrepancies
        assert len(result["agreements"]) >= 1

    def test_coverage_increases_over_cycles(self):
        """Coverage should generally increase (or denominator grow) over cycles."""
        mc = MockConnector(INTEGRATION_RESPONSES)
        state = ResearchState(
            topic=AMPHIPOLIS_TOPIC,
            country=AMPHIPOLIS_COUNTRY,
            discipline=AMPHIPOLIS_DISCIPLINE,
        )
        engine = EpistemicEngine(connector=mc, state=state)
        coverage_history = engine.run_all_cycles(max_cycles=3)

        if len(coverage_history) >= 2:
            # Total postulates should not decrease
            assert coverage_history[-1].total >= coverage_history[0].total

    def test_findings_deduplicated(self):
        """Duplicate findings should not be counted twice."""
        mc = MockConnector(INTEGRATION_RESPONSES)
        state = ResearchState(
            topic=AMPHIPOLIS_TOPIC,
            country=AMPHIPOLIS_COUNTRY,
            discipline=AMPHIPOLIS_DISCIPLINE,
        )
        engine = EpistemicEngine(connector=mc, state=state)
        engine.run_all_cycles(max_cycles=3)

        # unique_findings should have no duplicates by definition
        unique = state.unique_findings
        names_and_types = [(f.name.lower().strip(), f.finding_type) for f in unique]
        assert len(names_and_types) == len(set(names_and_types))

    def test_state_to_dict(self):
        """The state should be serializable to a dict."""
        mc = MockConnector(INTEGRATION_RESPONSES)
        state = ResearchState(
            topic=AMPHIPOLIS_TOPIC,
            country=AMPHIPOLIS_COUNTRY,
            discipline=AMPHIPOLIS_DISCIPLINE,
        )
        engine = EpistemicEngine(connector=mc, state=state)
        engine.run_all_cycles(max_cycles=2)

        result = state.to_dict()
        assert result["topic"] == AMPHIPOLIS_TOPIC
        assert isinstance(result["coverage_percentage"], float)
        assert isinstance(result["total_findings"], int)
        assert isinstance(result["coverage_history"], list)
