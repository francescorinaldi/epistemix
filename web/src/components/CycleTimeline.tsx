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
                  <svg width="12" height="12" viewBox="0 0 12 12">
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
              <svg width="12" height="12" viewBox="0 0 12 12">
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
          padding: 0.5rem 0;
          position: relative;
        }
        .step::before {
          content: "";
          position: absolute;
          left: -1.25rem;
          top: 0;
          bottom: 0;
          width: 2px;
          background: #334155;
        }
        .step:first-child::before {
          top: 50%;
        }
        .step:last-child::before {
          bottom: 50%;
        }
        .dot {
          width: 24px;
          height: 24px;
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
          background: #6366f1;
          color: white;
        }
        .current .dot {
          background: #1e293b;
          border: 2px solid #6366f1;
        }
        .pending .dot {
          background: #1e293b;
          border: 2px solid #334155;
        }
        .pulse {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #6366f1;
          animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.5); }
        }
        .info {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-left: -0.75rem;
        }
        .label {
          color: #e2e8f0;
          font-size: 0.875rem;
          font-weight: 500;
        }
        .pending .label {
          color: #64748b;
        }
        .coverage {
          color: #6366f1;
          font-weight: 700;
          font-size: 0.875rem;
        }
        .running {
          color: #f59e0b;
          font-size: 0.75rem;
          animation: blink 1s ease-in-out infinite;
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
