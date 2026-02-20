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
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="cycle"
            stroke="#94a3b8"
            label={{ value: "Cycle", position: "insideBottom", offset: -5, fill: "#94a3b8" }}
          />
          <YAxis
            domain={[0, 100]}
            stroke="#94a3b8"
            label={{ value: "Coverage %", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
          />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "0.5rem" }}
            labelStyle={{ color: "#94a3b8" }}
            itemStyle={{ color: "#6366f1" }}
            formatter={(value: number) => [`${value}%`, "Coverage"]}
          />
          <Line
            type="monotone"
            dataKey="percentage"
            stroke="#6366f1"
            strokeWidth={2.5}
            dot={{ fill: "#6366f1", r: 4 }}
            activeDot={{ r: 6 }}
          />
          {multiAgentCoverage !== undefined && (
            <ReferenceLine
              y={multiAgentCoverage}
              stroke="#f97316"
              strokeDasharray="5 5"
              label={{
                value: `Multi-agent: ${multiAgentCoverage}%`,
                fill: "#f97316",
                fontSize: 12,
                position: "right",
              }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      <style jsx>{`
        .chart-container {
          background: #0f172a;
          border: 1px solid #1e293b;
          border-radius: 0.75rem;
          padding: 1.25rem;
        }
        h3 {
          color: #e2e8f0;
          font-size: 1rem;
          margin: 0 0 0.75rem 0;
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
