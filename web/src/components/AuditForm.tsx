"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { canStartAudit, maxCyclesForPlan } from "@/lib/stripe";

const DISCIPLINES = [
  "archaeology",
  "history",
  "biology",
  "physics",
  "chemistry",
  "medicine",
  "computer science",
  "economics",
  "sociology",
  "psychology",
  "political science",
  "philosophy",
  "linguistics",
  "engineering",
  "environmental science",
  "other",
];

export default function AuditForm() {
  const router = useRouter();
  const { profile } = useAuth();
  const [topic, setTopic] = useState("");
  const [country, setCountry] = useState("");
  const [discipline, setDiscipline] = useState("archaeology");
  const [cycles, setCycles] = useState(4);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const plan = profile?.plan ?? "free";
  const maxCycles = maxCyclesForPlan(plan);
  const canStart = profile
    ? canStartAudit(plan, profile.audits_this_month)
    : false;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!topic.trim() || !country.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch("/api/v1/audits", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: topic.trim(),
          country: country.trim(),
          discipline,
          max_cycles: Math.min(cycles, maxCycles),
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to start audit");
      }

      const { id } = await res.json();
      router.push(`/audit/${id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="audit-form">
      <div className="form-group">
        <label htmlFor="topic">Research Topic</label>
        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g., Amphipolis tomb excavation"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="country">Country</label>
        <input
          id="country"
          type="text"
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          placeholder="e.g., Greece"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="discipline">Discipline</label>
        <select
          id="discipline"
          value={discipline}
          onChange={(e) => setDiscipline(e.target.value)}
        >
          {DISCIPLINES.map((d) => (
            <option key={d} value={d}>
              {d.charAt(0).toUpperCase() + d.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="cycles">
          Max Cycles ({plan === "free" ? `${maxCycles} on free plan` : maxCycles})
        </label>
        <input
          id="cycles"
          type="range"
          min={1}
          max={maxCycles}
          value={Math.min(cycles, maxCycles)}
          onChange={(e) => setCycles(Number(e.target.value))}
        />
        <span className="cycle-count">{Math.min(cycles, maxCycles)}</span>
      </div>

      {error && <p className="error">{error}</p>}

      <button type="submit" disabled={submitting || !canStart}>
        {submitting
          ? "Starting..."
          : !canStart
            ? "Monthly limit reached"
            : "Start Epistemic Audit"}
      </button>

      {!canStart && profile && (
        <p className="upgrade-hint">
          Upgrade to Pro for unlimited audits.
        </p>
      )}

      <style jsx>{`
        .audit-form {
          max-width: 480px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }
        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.375rem;
        }
        label {
          font-size: 0.875rem;
          font-weight: 600;
          color: #e2e8f0;
        }
        input[type="text"],
        select {
          padding: 0.625rem 0.75rem;
          border: 1px solid #334155;
          border-radius: 0.5rem;
          background: #1e293b;
          color: #f1f5f9;
          font-size: 0.9375rem;
        }
        input[type="text"]:focus,
        select:focus {
          outline: none;
          border-color: #6366f1;
          box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25);
        }
        input[type="range"] {
          flex: 1;
        }
        .cycle-count {
          font-weight: 700;
          color: #6366f1;
          font-size: 1.125rem;
        }
        button {
          padding: 0.75rem;
          border: none;
          border-radius: 0.5rem;
          background: #6366f1;
          color: white;
          font-weight: 600;
          font-size: 1rem;
          cursor: pointer;
          transition: background 0.2s;
        }
        button:hover:not(:disabled) {
          background: #4f46e5;
        }
        button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .error {
          color: #f87171;
          font-size: 0.875rem;
        }
        .upgrade-hint {
          text-align: center;
          color: #94a3b8;
          font-size: 0.8125rem;
        }
      `}</style>
    </form>
  );
}
