"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { CoveragePoint } from "@/lib/types";

interface Props {
  history: CoveragePoint[];
  multiAgentCoverage?: number;
}

export default function CoverageChart({ history, multiAgentCoverage }: Props) {
  if (history.length === 0) {
    return <div className="empty">No coverage data yet...</div>;
  }

  return (
    <div className="chart-container">
      <h3>Coverage Over Cycles</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={history} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey="cycle"
            stroke="var(--text-ghost)"
            label={{ value: "Cycle", position: "insideBottom", offset: -5, fill: "var(--text-ghost)" }}
          />
          <YAxis
            domain={[0, 100]}
            stroke="var(--text-ghost)"
            label={{ value: "Coverage %", angle: -90, position: "insideLeft", fill: "var(--text-ghost)" }}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: '8px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
            }}
            labelStyle={{ color: 'var(--text-tertiary)' }}
            itemStyle={{ color: 'var(--chart-1)' }}
            formatter={(value: number) => [`${value}%`, "Coverage"]}
          />
          <Line
            type="monotone"
            dataKey="percentage"
            stroke="var(--chart-1)"
            strokeWidth={2}
            dot={{ fill: "var(--chart-1)", r: 3 }}
            activeDot={{ r: 5 }}
          />
          {multiAgentCoverage !== undefined && (
            <ReferenceLine
              y={multiAgentCoverage}
              stroke="var(--accent)"
              strokeDasharray="5 5"
              label={{
                value: `Multi-agent: ${multiAgentCoverage}%`,
                fill: "var(--accent)",
                fontSize: 11,
                position: "right",
              }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      <style jsx>{`
        .chart-container {
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
        .empty {
          color: var(--text-ghost);
          text-align: center;
          padding: 2rem;
        }
      `}</style>
    </div>
  );
}
