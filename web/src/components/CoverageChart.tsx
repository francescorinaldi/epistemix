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
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
          <XAxis
            dataKey="cycle"
            stroke="var(--text-ghost)"
            tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }}
            tickLine={{ stroke: 'var(--border-subtle)' }}
            axisLine={{ stroke: 'var(--border-subtle)' }}
            label={{ value: "Cycle", position: "insideBottom", offset: -5, fill: "var(--text-ghost)", fontSize: 10 }}
          />
          <YAxis
            domain={[0, 100]}
            stroke="var(--text-ghost)"
            tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }}
            tickLine={{ stroke: 'var(--border-subtle)' }}
            axisLine={{ stroke: 'var(--border-subtle)' }}
            label={{ value: "Coverage %", angle: -90, position: "insideLeft", fill: "var(--text-ghost)", fontSize: 10 }}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.6875rem',
              padding: '0.5rem 0.75rem',
            }}
            labelStyle={{ color: 'var(--text-tertiary)', fontSize: '0.625rem' }}
            itemStyle={{ color: 'var(--chart-1)' }}
            formatter={(value: number) => [`${value}%`, "Coverage"]}
            cursor={{ stroke: 'rgba(255,255,255,0.04)' }}
          />
          <Line
            type="monotone"
            dataKey="percentage"
            stroke="var(--chart-1)"
            strokeWidth={1.5}
            dot={{ fill: "var(--chart-1)", r: 2.5, strokeWidth: 0 }}
            activeDot={{ r: 4, strokeWidth: 0 }}
          />
          {multiAgentCoverage !== undefined && (
            <ReferenceLine
              y={multiAgentCoverage}
              stroke="var(--accent-dim)"
              strokeDasharray="4 4"
              strokeWidth={1}
              label={{
                value: `Multi-agent: ${multiAgentCoverage}%`,
                fill: "var(--accent-dim)",
                fontSize: 10,
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
          padding: 2rem;
        }
        h3 {
          font-family: var(--font-display);
          font-size: 1rem;
          color: var(--text-heading);
          margin: 0 0 1.25rem 0;
          font-weight: 400;
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
