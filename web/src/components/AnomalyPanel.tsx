"use client";

import type { AnomalyData } from "@/lib/types";

interface Props {
  anomalies: AnomalyData[];
}

const SEVERITY_STYLES: Record<string, { border: string; text: string; icon: string }> = {
  critical: { border: "var(--danger)", text: "var(--danger)", icon: "!!" },
  high: { border: "var(--warning)", text: "var(--warning)", icon: "!" },
  medium: { border: "var(--text-ghost)", text: "var(--text-secondary)", icon: "~" },
};

const TYPE_LABELS: Record<string, string> = {
  language_gap: "Language Gap",
  theory_gap: "Theory Gap",
  discipline_gap: "Discipline Gap",
  institution_gap: "Institution Gap",
  school_gap: "School Gap",
  publication_gap: "Publication Gap",
  temporal_gap: "Temporal Gap",
  citation_island: "Citation Island",
  convergence_excess: "Echo Chamber",
  divergence_excess: "Fragmentation",
  structural_absence: "Structural Absence",
  empty_query_pattern: "Empty Query Pattern",
};

export default function AnomalyPanel({ anomalies }: Props) {
  if (anomalies.length === 0) {
    return <div className="empty">No anomalies detected yet.</div>;
  }

  const sorted = [...anomalies].sort((a, b) => {
    const order = { critical: 0, high: 1, medium: 2 };
    return (order[a.severity] ?? 3) - (order[b.severity] ?? 3);
  });

  const counts = {
    critical: anomalies.filter((a) => a.severity === "critical").length,
    high: anomalies.filter((a) => a.severity === "high").length,
    medium: anomalies.filter((a) => a.severity === "medium").length,
  };

  return (
    <div className="panel">
      <div className="header">
        <h3>Anomalies ({anomalies.length})</h3>
        <div className="badges">
          {counts.critical > 0 && (
            <span className="badge critical">{counts.critical} critical</span>
          )}
          {counts.high > 0 && (
            <span className="badge high">{counts.high} high</span>
          )}
          {counts.medium > 0 && (
            <span className="badge medium">{counts.medium} medium</span>
          )}
        </div>
      </div>

      <div className="list">
        {sorted.map((anomaly, i) => {
          const style = SEVERITY_STYLES[anomaly.severity] ?? SEVERITY_STYLES.medium;
          return (
            <div
              key={anomaly.id || i}
              className="anomaly"
              style={{
                borderLeft: `2px solid ${style.border}`,
              }}
            >
              <div className="anomaly-header">
                <span className="icon" style={{ color: style.text }}>
                  {style.icon}
                </span>
                <span className="type">
                  {TYPE_LABELS[anomaly.anomaly_type] || anomaly.anomaly_type}
                </span>
                <span className="severity" style={{ color: style.text }}>
                  {anomaly.severity}
                </span>
              </div>
              <p className="description">{anomaly.description}</p>
              {anomaly.suggested_queries.length > 0 && (
                <div className="suggestions">
                  {anomaly.suggested_queries.map((q, j) => (
                    <span key={j} className="suggestion">
                      {q}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <style jsx>{`
        .panel {
          background: var(--bg-card);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-lg);
          padding: 2rem;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          margin-bottom: 1.25rem;
        }
        h3 {
          font-family: var(--font-display);
          font-size: 1rem;
          color: var(--text-heading);
          margin: 0;
          font-weight: 400;
        }
        .badges {
          display: flex;
          gap: 0.375rem;
        }
        .badge {
          font-family: var(--font-mono);
          font-size: 0.5625rem;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          padding: 0.0625rem 0.375rem;
          border-radius: var(--radius-sm);
        }
        .badge.critical {
          background: var(--danger-bg);
          color: var(--danger);
        }
        .badge.high {
          background: var(--warning-bg);
          color: var(--warning);
        }
        .badge.medium {
          background: rgba(255,255,255,0.02);
          color: var(--text-tertiary);
        }
        .list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .anomaly {
          padding: 0.625rem 0.625rem 0.625rem 0.875rem;
          border-radius: 0;
        }
        .anomaly-header {
          display: flex;
          align-items: center;
          gap: 0.375rem;
          margin-bottom: 0.25rem;
        }
        .icon {
          font-weight: 600;
          font-family: var(--font-mono);
          font-size: 0.6875rem;
        }
        .type {
          font-family: var(--font-body);
          font-weight: 500;
          font-size: 0.8125rem;
          color: var(--text-heading);
        }
        .severity {
          font-family: var(--font-mono);
          font-size: 0.5625rem;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          margin-left: auto;
        }
        .description {
          font-family: var(--font-body);
          font-size: 0.8125rem;
          color: var(--text-secondary);
          line-height: 1.5;
          margin: 0;
        }
        .suggestions {
          display: flex;
          flex-wrap: wrap;
          gap: 0.25rem;
          margin-top: 0.5rem;
        }
        .suggestion {
          font-family: var(--font-mono);
          font-size: 0.5625rem;
          background: var(--accent-bg);
          color: var(--accent-dim);
          border: 1px solid var(--accent-border);
          border-radius: var(--radius-sm);
          padding: 0.0625rem 0.375rem;
        }
        .empty {
          color: var(--text-ghost);
          font-family: var(--font-body);
          font-size: 0.8125rem;
          text-align: center;
          padding: 3rem 2rem;
        }
      `}</style>
    </div>
  );
}
