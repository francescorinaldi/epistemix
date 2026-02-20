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

  const plan = (profile?.plan ?? "free") as "free" | "pro" | "enterprise";
  const maxCycles = maxCyclesForPlan(plan);
  const canStart = profile
    ? canStartAudit(plan, profile.audits_this_month)
    : false;

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
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
          gap: 1.5rem;
        }
        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.375rem;
        }
        label {
          font-family: var(--font-mono);
          font-size: 0.75rem;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--text-secondary);
        }
        input[type="text"],
        select {
          padding: 0.75rem 0.875rem;
          background: var(--bg-card);
          border: 1px solid var(--border-default);
          border-radius: var(--radius-sm);
          color: var(--text-heading);
          font-family: var(--font-body);
          font-size: 0.9375rem;
        }
        input[type="text"]:focus,
        select:focus {
          outline: none;
          border-color: var(--accent);
          box-shadow: 0 0 0 2px var(--accent-bg);
        }
        input[type="range"] {
          flex: 1;
          accent-color: var(--accent);
        }
        .cycle-count {
          font-family: var(--font-mono);
          font-size: 1.125rem;
          font-weight: 700;
          color: var(--accent);
        }
        button {
          padding: 0.875rem;
          border: none;
          border-radius: var(--radius-md);
          background: var(--accent);
          color: #0b0e15;
          font-weight: 600;
          font-family: var(--font-body);
          font-size: 0.9375rem;
          cursor: pointer;
          transition: filter 0.2s, transform 0.2s;
        }
        button:hover:not(:disabled) {
          filter: brightness(1.1);
          transform: translateY(-1px);
        }
        button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .error {
          color: var(--danger);
          font-size: 0.8125rem;
        }
        .upgrade-hint {
          font-family: var(--font-mono);
          font-size: 0.75rem;
          color: var(--text-tertiary);
          text-align: center;
        }
      `}</style>
    </form>
  );
}
