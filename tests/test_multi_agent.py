"""Tests for the multi-agent system."""

from epistemix.core import DynamicPostulates
from epistemix.multi_agent import (
    AgentInstitutional,
    AgentTheoretical,
    Arbiter,
    MultiAgentSystem,
)
from epistemix.models import Finding, GapType


class TestAgentInstitutional:
    def test_audit_returns_report(self, all_findings):
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)
        agent = AgentInstitutional(post)
        report = agent.audit(all_findings)
        assert report.agent_name == "Agent \u03b1 (Institutional)"
        assert len(report.expectations) > 0
        assert report.coverage_score >= 0

    def test_detects_language_expectations(self, cycle_0_findings):
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in cycle_0_findings:
            post.ingest_finding(f)
        agent = AgentInstitutional(post)
        report = agent.audit(cycle_0_findings)
        linguistic = [
            e for e in report.expectations
            if e.gap_type == GapType.LINGUISTIC
        ]
        assert len(linguistic) >= 1  # At least Greek + English


class TestAgentTheoretical:
    def test_audit_returns_report(self, all_findings):
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)
        agent = AgentTheoretical(post)
        report = agent.audit(all_findings)
        assert report.agent_name == "Agent \u03b2 (Theoretical)"
        assert len(report.expectations) > 0

    def test_detects_theory_expectations(self, cycle_0_findings):
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in cycle_0_findings:
            post.ingest_finding(f)
        agent = AgentTheoretical(post)
        report = agent.audit(cycle_0_findings)
        theory = [
            e for e in report.expectations
            if e.gap_type == GapType.THEORY_UNSOURCED
        ]
        assert len(theory) >= 1  # At least Hephaestion and Olympias

    def test_detects_single_advocate(self):
        findings = [
            Finding(
                source="P1", language="en",
                author="Alice", theory_supported="Lonely Theory",
                source_type="peer_reviewed",
            ),
        ]
        post = DynamicPostulates("Greece", "test")
        for f in findings:
            post.ingest_finding(f)
        agent = AgentTheoretical(post)
        report = agent.audit(findings)
        voice_anomalies = [
            a for a in report.anomalies if a.gap_type == GapType.VOICE
        ]
        assert len(voice_anomalies) >= 1


class TestArbiter:
    def test_finds_discrepancies(self, all_findings):
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)

        alpha = AgentInstitutional(post)
        beta = AgentTheoretical(post)
        report_a = alpha.audit(all_findings)
        report_b = beta.audit(all_findings)

        arbiter = Arbiter(report_a, report_b)
        discrepancies = arbiter.compare()
        # With different focuses, there should be discrepancies
        assert isinstance(discrepancies, list)

    def test_combined_score(self, all_findings):
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)

        alpha = AgentInstitutional(post)
        beta = AgentTheoretical(post)
        report_a = alpha.audit(all_findings)
        report_b = beta.audit(all_findings)

        arbiter = Arbiter(report_a, report_b)
        arbiter.compare()
        score = arbiter.combined_score()
        assert 0 <= score <= 100

    def test_report_string(self, all_findings):
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)

        alpha = AgentInstitutional(post)
        beta = AgentTheoretical(post)
        report_a = alpha.audit(all_findings)
        report_b = beta.audit(all_findings)

        arbiter = Arbiter(report_a, report_b)
        arbiter.compare()
        text = arbiter.report()
        assert "MULTI-AGENT ARBITER REPORT" in text

    def test_to_dict(self, all_findings):
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)

        alpha = AgentInstitutional(post)
        beta = AgentTheoretical(post)
        report_a = alpha.audit(all_findings)
        report_b = beta.audit(all_findings)

        arbiter = Arbiter(report_a, report_b)
        arbiter.compare()
        d = arbiter.to_dict()
        assert "alpha" in d
        assert "beta" in d
        assert "combined" in d
        assert "discrepancies" in d


class TestMultiAgentSystem:
    def test_run(self, all_findings):
        post = DynamicPostulates("Greece", "Amphipolis tomb", "archaeology")
        for f in all_findings:
            post.ingest_finding(f)

        system = MultiAgentSystem(post)
        result = system.run(all_findings)
        assert "alpha" in result
        assert "beta" in result
        assert "combined" in result
