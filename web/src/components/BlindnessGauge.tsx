"use client";

import type { MultiAgentResult } from "@/lib/types";

interface Props {
  result: MultiAgentResult;
}

export default function BlindnessGauge({ result }: Props) {
  const { alpha, beta, combined } = result;

  return (
    <div className="gauge">
      <h3>Multi-Agent Analysis</h3>

      <div className="meters">
        <div className="meter">
          <div className="meter-label">
            <span>Agent Alpha (Institutional)</span>
            <span className="value">{alpha.coverage}%</span>
          </div>
          <div className="bar">
            <div
              className="fill alpha"
              style={{ width: `${Math.min(alpha.coverage, 100)}%` }}
            />
          </div>
        </div>

        <div className="meter">
          <div className="meter-label">
            <span>Agent Beta (Theoretical)</span>
            <span className="value">{beta.coverage}%</span>
          </div>
          <div className="bar">
            <div
              className="fill beta"
              style={{ width: `${Math.min(beta.coverage, 100)}%` }}
            />
          </div>
        </div>

        <div className="meter">
          <div className="meter-label">
            <span>Combined Coverage</span>
            <span className="value combined-value">{combined.coverage}%</span>
          </div>
          <div className="bar">
            <div
              className="fill combined"
              style={{ width: `${Math.min(combined.coverage, 100)}%` }}
            />
          </div>
        </div>
      </div>

      <div className="stats">
        <div className="stat blindness">
          <div className="stat-value">{combined.blindness_gap}</div>
          <div className="stat-label">Blindness Gap (points)</div>
        </div>
        <div className="stat">
          <div className="stat-value">{combined.total_anomalies}</div>
          <div className="stat-label">Total Anomalies</div>
        </div>
        <div className="stat">
          <div className="stat-value">{combined.known_unknowns}</div>
          <div className="stat-label">Known Unknowns</div>
        </div>
      </div>

      {result.known_unknowns.length > 0 && (
        <div className="unknowns">
          <h4>Known Unknowns</h4>
          {result.known_unknowns.map((ku, i) => (
            <div key={i} className="unknown">
              <span className="unknown-severity">{ku.severity}</span>
              <span className="unknown-desc">{ku.description}</span>
            </div>
          ))}
        </div>
      )}

      <style jsx>{`
        .gauge {
          background: var(--bg-card);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-lg);
          padding: 1.5rem;
        }
        h3 {
          font-family: var(--font-display);
          font-size: 1.125rem;
          color: var(--text-heading);
          margin: 0 0 1rem 0;
          font-weight: 400;
        }
        h4 {
          font-family: var(--font-display);
          font-size: 1rem;
          color: var(--text-heading);
          margin: 0 0 0.5rem 0;
          font-weight: 400;
        }
        .meters {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          margin-bottom: 1.25rem;
        }
        .meter-label {
          display: flex;
          justify-content: space-between;
          font-family: var(--font-mono);
          font-size: 0.75rem;
          color: var(--text-tertiary);
          margin-bottom: 0.25rem;
        }
        .value {
          font-family: var(--font-mono);
          font-weight: 700;
          color: var(--text-heading);
        }
        .combined-value {
          color: var(--accent);
        }
        .bar {
          height: 5px;
          background: var(--bg-hover);
          border-radius: 3px;
          overflow: hidden;
        }
        .fill {
          height: 100%;
          border-radius: 3px;
          transition: width 0.5s ease;
        }
        .fill.alpha {
          background: var(--chart-1);
        }
        .fill.beta {
          background: var(--chart-4);
        }
        .fill.combined {
          background: var(--accent);
        }
        .stats {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 0.75rem;
          margin-bottom: 1rem;
        }
        .stat {
          text-align: center;
          padding: 0.75rem;
          background: var(--bg-elevated);
          border-radius: var(--radius-md);
        }
        .stat.blindness {
          border: 1px solid var(--accent-border);
        }
        .stat-value {
          font-family: var(--font-mono);
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text-heading);
        }
        .blindness .stat-value {
          color: var(--accent);
        }
        .stat-label {
          font-family: var(--font-mono);
          font-size: 0.5625rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--text-tertiary);
          margin-top: 0.125rem;
        }
        .unknowns {
          border-top: 1px solid var(--border-subtle);
          padding-top: 1rem;
          margin-top: 0.5rem;
        }
        .unknown {
          display: flex;
          gap: 0.5rem;
          padding: 0.375rem 0;
        }
        .unknown-severity {
          font-family: var(--font-mono);
          font-size: 0.625rem;
          font-weight: 600;
          text-transform: uppercase;
          color: var(--danger);
          min-width: 4rem;
        }
        .unknown-desc {
          font-size: 0.8125rem;
          color: var(--text-secondary);
        }
      `}</style>
    </div>
  );
}
