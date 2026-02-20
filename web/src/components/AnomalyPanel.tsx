"use client";

import type { AnomalyData } from "@/lib/types";

interface Props {
  anomalies: AnomalyData[];
}

const SEVERITY_STYLES: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  critical: { bg: "#450a0a", border: "#991b1b", text: "#fca5a5", icon: "!!" },
  high: { bg: "#451a03", border: "#92400e", text: "#fed7aa", icon: "!" },
  medium: { bg: "#1a2332", border: "#334155", text: "#94a3b8", icon: "~" },
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
                background: style.bg,
                borderLeft: `3px solid ${style.border}`,
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
          background: #0f172a;
          border: 1px solid #1e293b;
          border-radius: 0.75rem;
          padding: 1.25rem;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }
        h3 {
          color: #e2e8f0;
          font-size: 1rem;
          margin: 0;
        }
        .badges {
          display: flex;
          gap: 0.5rem;
        }
        .badge {
          font-size: 0.75rem;
          padding: 0.125rem 0.5rem;
          border-radius: 999px;
          font-weight: 600;
        }
        .badge.critical {
          background: #450a0a;
          color: #fca5a5;
        }
        .badge.high {
          background: #451a03;
          color: #fed7aa;
        }
        .badge.medium {
          background: #1a2332;
          color: #94a3b8;
        }
        .list {
          display: flex;
          flex-direction: column;
          gap: 0.625rem;
        }
        .anomaly {
          padding: 0.75rem;
          border-radius: 0.375rem;
        }
        .anomaly-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.375rem;
        }
        .icon {
          font-weight: 700;
          font-family: monospace;
        }
        .type {
          color: #e2e8f0;
          font-weight: 600;
          font-size: 0.875rem;
        }
        .severity {
          font-size: 0.75rem;
          text-transform: uppercase;
          margin-left: auto;
        }
        .description {
          color: #cbd5e1;
          font-size: 0.8125rem;
          margin: 0;
          line-height: 1.4;
        }
        .suggestions {
          display: flex;
          flex-wrap: wrap;
          gap: 0.375rem;
          margin-top: 0.5rem;
        }
        .suggestion {
          font-size: 0.6875rem;
          background: rgba(99, 102, 241, 0.15);
          color: #a5b4fc;
          padding: 0.125rem 0.5rem;
          border-radius: 999px;
        }
        .empty {
          color: #64748b;
          text-align: center;
          padding: 2rem;
        }
      `}</style>
    </div>
  );
}
