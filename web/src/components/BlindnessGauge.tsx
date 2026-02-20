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
          background: #0f172a;
          border: 1px solid #1e293b;
          border-radius: 0.75rem;
          padding: 1.25rem;
        }
        h3 {
          color: #e2e8f0;
          font-size: 1rem;
          margin: 0 0 1rem 0;
        }
        h4 {
          color: #e2e8f0;
          font-size: 0.875rem;
          margin: 0 0 0.5rem 0;
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
          font-size: 0.8125rem;
          color: #94a3b8;
          margin-bottom: 0.25rem;
        }
        .value {
          font-weight: 700;
          color: #e2e8f0;
        }
        .combined-value {
          color: #f97316;
        }
        .bar {
          height: 8px;
          background: #1e293b;
          border-radius: 4px;
          overflow: hidden;
        }
        .fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.5s ease;
        }
        .fill.alpha {
          background: #6366f1;
        }
        .fill.beta {
          background: #8b5cf6;
        }
        .fill.combined {
          background: #f97316;
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
          background: #1e293b;
          border-radius: 0.5rem;
        }
        .stat.blindness {
          border: 1px solid #f97316;
        }
        .stat-value {
          font-size: 1.5rem;
          font-weight: 700;
          color: #e2e8f0;
        }
        .blindness .stat-value {
          color: #f97316;
        }
        .stat-label {
          font-size: 0.6875rem;
          color: #64748b;
          margin-top: 0.125rem;
        }
        .unknowns {
          border-top: 1px solid #1e293b;
          padding-top: 1rem;
        }
        .unknown {
          display: flex;
          gap: 0.5rem;
          padding: 0.375rem 0;
          font-size: 0.8125rem;
        }
        .unknown-severity {
          color: #f87171;
          font-weight: 600;
          text-transform: uppercase;
          font-size: 0.6875rem;
          min-width: 4rem;
        }
        .unknown-desc {
          color: #cbd5e1;
        }
      `}</style>
    </div>
  );
}
