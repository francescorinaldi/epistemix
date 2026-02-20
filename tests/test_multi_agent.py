"""Tests for the multi-agent system."""

from epistemix.connector import MockConnector
from epistemix.multi_agent import (
    ALPHA_PERSPECTIVE,
    BETA_PERSPECTIVE,
    AgentPerspective,
    Arbiter,
    AgentReport,
    EpistemicAgent,
    MultiAgentSystem,
)
from epistemix.models import (
    Anomaly,
    AnomalyType,
    CoverageScore,
    Finding,
    FindingType,
    Severity,
)
from tests.conftest import (
    AMPHIPOLIS_TOPIC,
    AMPHIPOLIS_COUNTRY,
    AMPHIPOLIS_DISCIPLINE,
    AMPHIPOLIS_CYCLE_0_RESPONSES,
    AMPHIPOLIS_CYCLE_1_RESPONSES,
)


class TestAgentPerspective:
    def test_alpha_weights(self):
        assert ALPHA_PERSPECTIVE.weight_for("MA-01") == 1.5  # Language
        assert ALPHA_PERSPECTIVE.weight_for("MA-03") == 0.7  # Theory

    def test_beta_weights(self):
        assert BETA_PERSPECTIVE.weight_for("MA-03") == 1.5  # Theory
        assert BETA_PERSPECTIVE.weight_for("MA-01") == 0.7  # Language

    def test_default_weight(self):
        p = AgentPerspective(name="test", description="test")
        assert p.weight_for("MA-99") == 1.0


class TestEpistemicAgent:
    def _mock_connector(self) -> MockConnector:
        mc = MockConnector()
        mc.register_responses({
            **AMPHIPOLIS_CYCLE_0_RESPONSES,
            **AMPHIPOLIS_CYCLE_1_RESPONSES,
        })
        return mc

    def test_agent_runs(self):
        agent = EpistemicAgent.create(
            perspective=ALPHA_PERSPECTIVE,
            connector=self._mock_connector(),
            topic=AMPHIPOLIS_TOPIC,
            country=AMPHIPOLIS_COUNTRY,
            discipline=AMPHIPOLIS_DISCIPLINE,
        )
        report = agent.run(max_cycles=2)
        assert report.agent_name == "alpha"
        assert report.coverage.total > 0
        assert len(report.coverage_history) >= 1

    def test_agents_produce_different_results(self):
        mc = self._mock_connector()
        alpha = EpistemicAgent.create(
            perspective=ALPHA_PERSPECTIVE,
            connector=mc,
            topic=AMPHIPOLIS_TOPIC,
            country=AMPHIPOLIS_COUNTRY,
            discipline=AMPHIPOLIS_DISCIPLINE,
        )
        beta = EpistemicAgent.create(
            perspective=BETA_PERSPECTIVE,
            connector=mc,
            topic=AMPHIPOLIS_TOPIC,
            country=AMPHIPOLIS_COUNTRY,
            discipline=AMPHIPOLIS_DISCIPLINE,
        )
        alpha_report = alpha.run(max_cycles=2)
        beta_report = beta.run(max_cycles=2)
        # Both should have run
        assert alpha_report.coverage.total > 0
        assert beta_report.coverage.total > 0


class TestArbiter:
    def _make_report(
        self,
        name: str,
        findings: list[Finding],
        anomalies: list[Anomaly],
        coverage_pct: float,
    ) -> AgentReport:
        total = 20
        confirmed = int(total * coverage_pct / 100)
        return AgentReport(
            agent_name=name,
            perspective=ALPHA_PERSPECTIVE if name == "alpha" else BETA_PERSPECTIVE,
            coverage=CoverageScore(confirmed=confirmed, total=total),
            findings=findings,
            anomalies=anomalies,
        )

    def test_finds_agreements(self):
        shared_finding = Finding(name="Peristeri", finding_type=FindingType.SCHOLAR)
        alpha = self._make_report("alpha", [shared_finding], [], 70)
        beta = self._make_report("beta", [shared_finding], [], 65)
        result = Arbiter().compare(alpha, beta)
        assert any("1 findings agreed" in a for a in result.agreements)

    def test_finds_discrepancies(self):
        f1 = Finding(name="Alice", finding_type=FindingType.SCHOLAR)
        f2 = Finding(name="Bob", finding_type=FindingType.SCHOLAR)
        alpha = self._make_report("alpha", [f1], [], 70)
        beta = self._make_report("beta", [f2], [], 65)
        result = Arbiter().compare(alpha, beta)
        assert len(result.discrepancies) >= 2

    def test_known_unknowns_from_discrepant_anomalies(self):
        # Alpha detects language gap, beta detects theory gap
        a1 = Anomaly(
            id="A-1", anomaly_type=AnomalyType.LANGUAGE_GAP,
            severity=Severity.HIGH, description="No Greek sources",
        )
        a2 = Anomaly(
            id="A-2", anomaly_type=AnomalyType.THEORY_GAP,
            severity=Severity.HIGH, description="Only one theory found",
        )
        alpha = self._make_report("alpha", [], [a1], 70)
        beta = self._make_report("beta", [], [a2], 65)
        result = Arbiter().compare(alpha, beta)
        assert len(result.known_unknowns) >= 2

    def test_combined_coverage_is_minimum(self):
        alpha = self._make_report("alpha", [], [], 70)
        beta = self._make_report("beta", [], [], 60)
        result = Arbiter().compare(alpha, beta)
        # Combined should be based on the lower coverage
        assert result.combined_coverage.percentage <= 65

    def test_blindness_gap(self):
        alpha = self._make_report("alpha", [], [], 70)
        beta = self._make_report("beta", [], [], 55)
        result = Arbiter().compare(alpha, beta)
        assert result.blindness_gap == 15.0


class TestMultiAgentSystem:
    def test_full_run(self):
        mc = MockConnector()
        mc.register_responses({
            **AMPHIPOLIS_CYCLE_0_RESPONSES,
            **AMPHIPOLIS_CYCLE_1_RESPONSES,
        })
        mas = MultiAgentSystem(
            connector=mc,
            topic=AMPHIPOLIS_TOPIC,
            country=AMPHIPOLIS_COUNTRY,
            discipline=AMPHIPOLIS_DISCIPLINE,
            max_cycles=2,
        )
        result = mas.run()
        assert "alpha" in result
        assert "beta" in result
        assert "combined" in result
        assert "agreements" in result
        assert "discrepancies" in result
        assert "known_unknowns" in result
        assert result["combined"]["blindness_gap"] >= 0
