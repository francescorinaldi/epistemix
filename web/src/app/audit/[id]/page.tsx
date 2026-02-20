"use client";

import { use } from "react";
import Link from "next/link";
import { useAuditRealtime } from "@/hooks/useAuditRealtime";
import CoverageChart from "@/components/CoverageChart";
import AnomalyPanel from "@/components/AnomalyPanel";
import CycleTimeline from "@/components/CycleTimeline";
import BlindnessGauge from "@/components/BlindnessGauge";
import CitationGraph from "@/components/CitationGraph";

export default function AuditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { audit, loading, error } = useAuditRealtime(id);

  if (loading) {
    return (
      <div className="center">
        <div className="spinner" />
        <p>Loading audit...</p>
      </div>
    );
  }

  if (error || !audit) {
    return (
      <div className="center">
        <p className="error">Audit not found or access denied.</p>
        <Link href="/dashboard">Back to Dashboard</Link>
      </div>
    );
  }

  const isRunning = audit.status === "running";
  const isComplete = audit.status === "complete";
  const lastCoverage =
    audit.coverage_history.length > 0
      ? audit.coverage_history[audit.coverage_history.length - 1]
      : null;

  return (
    <main>
      <nav>
        <Link href="/dashboard" className="back">
          &larr; Dashboard
        </Link>
        <span className={`status ${audit.status}`}>{audit.status}</span>
      </nav>

      <header>
        <h1>{audit.topic}</h1>
        <p className="meta">
          {audit.country} &middot; {audit.discipline} &middot;{" "}
          {audit.max_cycles} cycles
        </p>
      </header>

      {audit.status === "failed" && (
        <div className="error-banner">
          <strong>Audit failed:</strong> {audit.error_message}
        </div>
      )}

      <div className="summary">
        <div className="stat">
          <div className="stat-value">{lastCoverage?.percentage ?? 0}%</div>
          <div className="stat-label">Coverage</div>
        </div>
        <div className="stat">
          <div className="stat-value">{audit.findings?.length ?? 0}</div>
          <div className="stat-label">Findings</div>
        </div>
        <div className="stat">
          <div className="stat-value">{audit.anomalies?.length ?? 0}</div>
          <div className="stat-label">Anomalies</div>
        </div>
        <div className="stat">
          <div className="stat-value">
            {audit.postulates?.filter((p) => p.status === "confirmed").length ??
              0}
            /{audit.postulates?.length ?? 0}
          </div>
          <div className="stat-label">Postulates</div>
        </div>
      </div>

      <div className="grid">
        <div className="col">
          <CycleTimeline
            coverageHistory={audit.coverage_history}
            currentCycle={audit.current_cycle}
            status={audit.status}
            maxCycles={audit.max_cycles}
          />
          <CoverageChart
            history={audit.coverage_history}
            multiAgentCoverage={audit.multi_agent_result?.combined?.coverage}
          />
          {audit.findings && audit.findings.length > 0 && (
            <CitationGraph findings={audit.findings} />
          )}
        </div>
        <div className="col">
          <AnomalyPanel anomalies={audit.anomalies ?? []} />
          {isComplete && audit.multi_agent_result && (
            <BlindnessGauge result={audit.multi_agent_result} />
          )}
        </div>
      </div>

      {isRunning && (
        <div className="running-indicator">
          <div className="pulse-dot" />
          Audit in progress &mdash; results update in real-time
        </div>
      )}

      <style jsx>{`
        main {
          max-width: 1120px;
          margin: 0 auto;
          padding: 0 1.5rem 4rem;
        }
        nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem 0;
        }
        .back {
          color: #94a3b8;
          font-size: 0.875rem;
        }
        .status {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          padding: 0.25rem 0.75rem;
          border-radius: 999px;
        }
        .status.pending { background: #451a03; color: #f59e0b; }
        .status.running { background: #1e1b4b; color: #a5b4fc; }
        .status.complete { background: #052e16; color: #4ade80; }
        .status.failed { background: #450a0a; color: #fca5a5; }
        header {
          margin-bottom: 2rem;
        }
        h1 {
          font-size: 1.75rem;
          font-weight: 700;
          margin-bottom: 0.375rem;
        }
        .meta {
          color: #64748b;
          font-size: 0.9375rem;
        }
        .error-banner {
          background: #450a0a;
          border: 1px solid #991b1b;
          color: #fca5a5;
          padding: 1rem;
          border-radius: 0.5rem;
          margin-bottom: 1.5rem;
        }
        .summary {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1rem;
          margin-bottom: 2rem;
        }
        .stat {
          background: #0f172a;
          border: 1px solid #1e293b;
          border-radius: 0.75rem;
          padding: 1rem;
          text-align: center;
        }
        .stat-value {
          font-size: 1.5rem;
          font-weight: 700;
          color: #f1f5f9;
        }
        .stat-label {
          font-size: 0.75rem;
          color: #64748b;
          margin-top: 0.25rem;
        }
        .grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.5rem;
        }
        .col {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }
        .running-indicator {
          position: fixed;
          bottom: 1.5rem;
          right: 1.5rem;
          background: #1e1b4b;
          border: 1px solid #4338ca;
          color: #a5b4fc;
          padding: 0.625rem 1rem;
          border-radius: 999px;
          font-size: 0.8125rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .pulse-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #6366f1;
          animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        .center {
          text-align: center;
          padding: 4rem;
          color: #64748b;
        }
        .spinner {
          width: 24px;
          height: 24px;
          border: 2px solid #334155;
          border-top-color: #6366f1;
          border-radius: 50%;
          margin: 0 auto 1rem;
          animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .error {
          color: #f87171;
        }
        @media (max-width: 768px) {
          .summary { grid-template-columns: repeat(2, 1fr); }
          .grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </main>
  );
}
