"use client";

import type { CoveragePoint } from "@/lib/types";

interface Props {
  coverageHistory: CoveragePoint[];
  currentCycle: number;
  status: string;
  maxCycles: number;
}

export default function CycleTimeline({
  coverageHistory,
  currentCycle,
  status,
  maxCycles,
}: Props) {
  const cycles = Array.from({ length: maxCycles }, (_, i) => i);

  return (
    <div className="timeline">
      <h3>Audit Progress</h3>
      <div className="steps">
        {cycles.map((cycle) => {
          const coveragePoint = coverageHistory.find((c) => c.cycle === cycle);
          const isComplete = coveragePoint !== undefined;
          const isCurrent = cycle === currentCycle && status === "running";
          const isPending = cycle > currentCycle || (!isComplete && !isCurrent);

          return (
            <div
              key={cycle}
              className={`step ${isComplete ? "complete" : ""} ${isCurrent ? "current" : ""} ${isPending ? "pending" : ""}`}
            >
              <div className="dot">
                {isComplete && (
                  <svg width="10" height="10" viewBox="0 0 12 12">
                    <path
                      d="M2 6L5 9L10 3"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                      strokeLinecap="round"
                    />
                  </svg>
                )}
                {isCurrent && <div className="pulse" />}
              </div>
              <div className="info">
                <span className="label">Cycle {cycle}</span>
                {coveragePoint && (
                  <span className="coverage">{coveragePoint.percentage}%</span>
                )}
                {isCurrent && <span className="running">Running...</span>}
              </div>
            </div>
          );
        })}

        <div
          className={`step ${status === "complete" ? "complete" : "pending"}`}
        >
          <div className="dot">
            {status === "complete" && (
              <svg width="10" height="10" viewBox="0 0 12 12">
                <path
                  d="M2 6L5 9L10 3"
                  stroke="currentColor"
                  strokeWidth="2"
                  fill="none"
                  strokeLinecap="round"
                />
              </svg>
            )}
          </div>
          <div className="info">
            <span className="label">Multi-Agent Analysis</span>
          </div>
        </div>
      </div>

      <style jsx>{`
        .timeline {
          background: var(--bg-card);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-lg);
          padding: 2rem;
        }
        h3 {
          font-family: var(--font-display);
          font-size: 1rem;
          color: var(--text-heading);
          margin: 0 0 1.25rem 0;
          font-weight: 400;
        }
        .steps {
          display: flex;
          flex-direction: column;
          gap: 0;
          position: relative;
          padding-left: 1.25rem;
        }
        .step {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.375rem 0;
          position: relative;
        }
        .step::before {
          content: "";
          position: absolute;
          left: -1.25rem;
          top: 0;
          bottom: 0;
          width: 1px;
          background: var(--border-subtle);
        }
        .step:first-child::before {
          top: 50%;
        }
        .step:last-child::before {
          bottom: 50%;
        }
        .dot {
          width: 18px;
          height: 18px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          left: -2rem;
          flex-shrink: 0;
          z-index: 1;
        }
        .complete .dot {
          background: var(--accent);
          color: var(--bg-page);
        }
        .current .dot {
          background: transparent;
          border: 1.5px solid var(--accent);
        }
        .pending .dot {
          background: transparent;
          border: 1px solid var(--border-subtle);
          width: 18px;
          height: 18px;
        }
        .pulse {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--accent);
          animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        .info {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-left: -0.75rem;
        }
        .label {
          font-family: var(--font-body);
          font-size: 0.8125rem;
          font-weight: 400;
          color: var(--text-primary);
        }
        .pending .label {
          color: var(--text-ghost);
        }
        .coverage {
          font-family: var(--font-mono);
          font-size: 0.75rem;
          font-weight: 500;
          color: var(--accent-dim);
        }
        .running {
          font-family: var(--font-mono);
          font-size: 0.625rem;
          color: var(--text-tertiary);
          animation: blink 1.5s ease-in-out infinite;
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
}
