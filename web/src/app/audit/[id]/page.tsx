"use client";

import { use } from "react";
import Link from "next/link";
import { useAuditRealtime } from "@/hooks/useAuditRealtime";
import CoverageChart from "@/components/CoverageChart";
import AnomalyPanel from "@/components/AnomalyPanel";
import CycleTimeline from "@/components/CycleTimeline";
import BlindnessGauge from "@/components/BlindnessGauge";
import CitationGraph from "@/components/CitationGraph";
import type { CoveragePoint, FindingData, AnomalyData, MultiAgentResult } from "@/lib/types";

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
        <p className="loading-text">Loading audit...</p>
        <style jsx>{`
          .center {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
            padding: 4rem 2rem;
          }
          .spinner {
            width: 24px;
            height: 24px;
            border: 2px solid var(--bg-hover);
            border-top-color: var(--accent);
            border-radius: 50%;
            margin-bottom: 1rem;
            animation: spin 0.8s linear infinite;
          }
          .loading-text {
            font-family: var(--font-mono);
            font-size: 0.8125rem;
            color: var(--text-tertiary);
          }
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error || !audit) {
    return (
      <div className="center">
        <p className="error-text">Audit not found or access denied.</p>
        <Link href="/dashboard" className="back-link">Back to Dashboard</Link>
        <style jsx>{`
          .center {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
            padding: 4rem 2rem;
            gap: 1rem;
          }
          .error-text {
            font-family: var(--font-mono);
            font-size: 0.875rem;
            color: var(--danger);
          }
          .back-link {
            font-family: var(--font-mono);
            font-size: 0.8125rem;
            color: var(--text-tertiary);
            transition: color 0.15s;
          }
          .back-link:hover {
            color: var(--text-primary);
          }
        `}</style>
      </div>
    );
  }

  const isRunning = audit.status === "running";
  const isComplete = audit.status === "complete";
  const coverageHistory = (audit.coverage_history ?? []) as unknown as CoveragePoint[];
  const lastCoverage =
    coverageHistory.length > 0
      ? coverageHistory[coverageHistory.length - 1]
      : null;
  const findings = (audit.findings ?? []) as unknown as FindingData[];
  const anomalies = (audit.anomalies ?? []) as unknown as AnomalyData[];
  const postulates = (audit.postulates ?? []) as unknown as Array<{ status: string }>;
  const multiAgentResult = audit.multi_agent_result as unknown as MultiAgentResult | null;

  return (
    <main>
      <nav>
        <Link href="/dashboard" className="back">
          &larr; Dashboard
        </Link>
        <span className={`status-badge status-${audit.status}`}>
          {audit.status}
        </span>
      </nav>

      <header>
        <h1>{audit.topic}</h1>
        <p className="meta">
          {audit.country} &middot; {audit.discipline} &middot;{" "}
          {audit.max_cycles} cycles
        </p>
        <div className="meta-line" />
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
          <div className="stat-value">{findings.length}</div>
          <div className="stat-label">Findings</div>
        </div>
        <div className="stat">
          <div className="stat-value">{anomalies.length}</div>
          <div className="stat-label">Anomalies</div>
        </div>
        <div className="stat">
          <div className="stat-value">
            {postulates.filter((p) => p.status === "confirmed").length}
            /{postulates.length}
          </div>
          <div className="stat-label">Postulates</div>
        </div>
      </div>

      <div className="grid">
        <div className="col">
          <CycleTimeline
            coverageHistory={coverageHistory}
            currentCycle={audit.current_cycle}
            status={audit.status}
            maxCycles={audit.max_cycles}
          />
          <CoverageChart
            history={coverageHistory}
            multiAgentCoverage={multiAgentResult?.combined?.coverage}
          />
          {findings.length > 0 && (
            <CitationGraph findings={findings} />
          )}
        </div>
        <div className="col">
          <AnomalyPanel anomalies={anomalies} />
          {isComplete && multiAgentResult && (
            <BlindnessGauge result={multiAgentResult} />
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
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 2rem 4rem;
          position: relative;
          z-index: 1;
        }

        /* ---- Nav ---- */
        nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem 0;
        }
        .back {
          font-family: var(--font-mono);
          font-size: 0.8125rem;
          color: var(--text-tertiary);
          text-decoration: none;
          transition: color 0.15s;
        }
        .back:hover {
          color: var(--text-primary);
        }

        /* ---- Status badges ---- */
        .status-badge {
          font-family: var(--font-mono);
          font-size: 0.6875rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          padding: 0.25rem 0.75rem;
          border-radius: 999px;
        }
        .status-pending {
          background: var(--warning-bg);
          border: 1px solid var(--warning-border);
          color: var(--warning);
        }
        .status-running {
          background: var(--info-bg);
          border: 1px solid var(--info-border);
          color: var(--info);
        }
        .status-complete {
          background: var(--success-bg);
          border: 1px solid var(--success-border);
          color: var(--success);
        }
        .status-failed {
          background: var(--danger-bg);
          border: 1px solid var(--danger-border);
          color: var(--danger);
        }

        /* ---- Header ---- */
        header {
          margin-bottom: 2rem;
        }
        h1 {
          font-family: var(--font-display);
          font-size: 2rem;
          font-weight: 400;
          color: var(--text-heading);
          margin-bottom: 0.375rem;
          line-height: 1.2;
        }
        .meta {
          font-size: 0.875rem;
          color: var(--text-tertiary);
        }
        .meta-line {
          margin-top: 0.75rem;
          height: 1px;
          background: linear-gradient(
            to right,
            var(--accent-border),
            transparent 60%
          );
        }

        /* ---- Error banner ---- */
        .error-banner {
          background: var(--danger-bg);
          border: 1px solid var(--danger-border);
          color: var(--danger);
          padding: 1rem;
          border-radius: var(--radius-md);
          margin-bottom: 1.5rem;
          font-size: 0.875rem;
        }

        /* ---- Summary stats ---- */
        .summary {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1rem;
          margin-bottom: 2rem;
        }
        .stat {
          background: var(--bg-card);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-lg);
          padding: 1.25rem;
          text-align: center;
        }
        .stat-value {
          font-family: var(--font-mono);
          font-size: 1.75rem;
          font-weight: 700;
          color: var(--text-heading);
          line-height: 1;
        }
        .stat-label {
          font-family: var(--font-mono);
          font-size: 0.625rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--text-tertiary);
          margin-top: 0.25rem;
        }

        /* ---- Grid ---- */
        .grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.25rem;
        }
        .col {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        /* ---- Running indicator ---- */
        .running-indicator {
          position: fixed;
          bottom: 1.5rem;
          right: 1.5rem;
          background: var(--bg-elevated);
          border: 1px solid var(--info-border);
          color: var(--info);
          padding: 0.625rem 1rem;
          border-radius: 999px;
          font-family: var(--font-mono);
          font-size: 0.75rem;
          letter-spacing: 0.04em;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          box-shadow: var(--shadow-elevated);
          z-index: 50;
        }
        .pulse-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--info);
          animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }

        /* ---- Responsive ---- */
        @media (max-width: 768px) {
          .summary {
            grid-template-columns: repeat(2, 1fr);
          }
          .grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </main>
  );
}
