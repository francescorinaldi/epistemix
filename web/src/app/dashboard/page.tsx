"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { createClient } from "@/lib/supabase";
import type { Audit, CoveragePoint } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const { user, profile, loading: authLoading } = useAuth();
  const [audits, setAudits] = useState<Audit[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/auth/login");
      return;
    }

    async function fetchAudits() {
      const supabase = createClient();
      const { data } = await supabase
        .from("audits")
        .select("*")
        .order("created_at", { ascending: false });
      setAudits(data || []);
      setLoading(false);
    }

    fetchAudits();
  }, [user, authLoading, router]);

  async function handleDelete(auditId: string) {
    if (!confirm("Delete this audit? This cannot be undone.")) return;
    setDeleting(auditId);
    try {
      const res = await fetch(`/api/v1/audits/${auditId}`, { method: "DELETE" });
      if (res.ok) {
        setAudits((prev) => prev.filter((a) => a.id !== auditId));
      }
    } finally {
      setDeleting(null);
    }
  }

  if (authLoading || loading) {
    return (
      <div className="loading-container">
        <span className="loading-text">Loading</span>
        <style jsx>{`
          .loading-container {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
          }
          .loading-text {
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--text-tertiary);
            letter-spacing: 0.1em;
            text-transform: uppercase;
          }
        `}</style>
      </div>
    );
  }

  return (
    <main>
      <nav>
        <Link href="/" className="logo">
          Epistemix
        </Link>
        <div className="nav-right">
          <span className="plan-badge">{profile?.plan ?? "free"}</span>
          <span className="usage">
            {profile?.audits_this_month ?? 0} audits this month
          </span>
        </div>
      </nav>

      <div className="header">
        <h1>Your Audits</h1>
        <Link href="/audit/new" className="new-btn">
          + New Audit
        </Link>
      </div>

      {audits.length === 0 ? (
        <div className="empty">
          <p className="empty-prompt">
            No audits yet.
          </p>
          <p className="empty-cta">
            Start your first epistemic audit to map the unknown.
          </p>
          <Link href="/audit/new" className="new-btn">
            Start Audit
          </Link>
        </div>
      ) : (
        <div className="grid">
          {audits.map((audit) => {
            const coverageHistory = audit.coverage_history as CoveragePoint[] | null;
            const lastCoverage =
              Array.isArray(coverageHistory) && coverageHistory.length > 0
                ? coverageHistory[coverageHistory.length - 1]
                : null;
            const findings = Array.isArray(audit.findings) ? audit.findings : [];
            const anomalies = Array.isArray(audit.anomalies) ? audit.anomalies : [];

            return (
              <div key={audit.id} className="card">
                <div className="card-header">
                  <span className={`status status-${audit.status}`}>
                    {audit.status}
                  </span>
                  <div className="card-header-right">
                    <span className="date">
                      {new Date(audit.created_at).toLocaleDateString()}
                    </span>
                    {audit.status !== "running" && (
                      <button
                        className="delete-btn"
                        onClick={() => handleDelete(audit.id)}
                        disabled={deleting === audit.id}
                        title="Delete audit"
                      >
                        {deleting === audit.id ? "..." : "\u00d7"}
                      </button>
                    )}
                  </div>
                </div>
                <Link href={`/audit/${audit.id}`} className="card-link">
                  <h3 className="topic">{audit.topic}</h3>
                  <p className="meta">
                    {audit.country} &middot; {audit.discipline}
                  </p>
                  <div className="stats-row">
                    <div className="stat">
                      <span className="stat-val">
                        {lastCoverage?.percentage ?? 0}%
                      </span>
                      <span className="stat-lbl">Coverage</span>
                    </div>
                    <div className="stat">
                      <span className="stat-val">
                        {findings.length}
                      </span>
                      <span className="stat-lbl">Findings</span>
                    </div>
                    <div className="stat">
                      <span className="stat-val">
                        {anomalies.length}
                      </span>
                      <span className="stat-lbl">Anomalies</span>
                    </div>
                  </div>
                </Link>
              </div>
            );
          })}
        </div>
      )}

      <style jsx>{`
        main {
          max-width: 1100px;
          margin: 0 auto;
          padding: 0 2.5rem 5rem;
          position: relative;
          z-index: 1;
        }

        /* ---- Nav ---- */
        nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 2rem 0;
          border-bottom: 1px solid var(--border-subtle);
          margin-bottom: 1rem;
        }
        .logo {
          font-family: var(--font-display);
          font-size: 1.25rem;
          font-weight: 400;
          color: var(--text-heading);
          text-decoration: none;
          transition: color 0.2s;
        }
        .logo:hover {
          color: var(--accent);
          text-decoration: none;
        }
        .nav-right {
          display: flex;
          align-items: center;
          gap: 1.25rem;
        }
        .plan-badge {
          font-family: var(--font-mono);
          font-size: 0.6875rem;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          font-weight: 500;
          padding: 0.1875rem 0.625rem;
          border-radius: 999px;
          background: var(--accent-bg);
          border: 1px solid var(--accent-border);
          color: var(--accent-dim);
        }
        .usage {
          font-family: var(--font-mono);
          font-size: 0.6875rem;
          color: var(--text-tertiary);
          letter-spacing: 0.02em;
        }

        /* ---- Header ---- */
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin: 3rem 0 2rem;
        }
        h1 {
          font-family: var(--font-display);
          font-size: 2.25rem;
          font-weight: 400;
          color: var(--text-heading);
        }
        .new-btn {
          display: inline-flex;
          align-items: center;
          padding: 0.625rem 1.5rem;
          background: var(--accent);
          color: #0a0d12;
          border-radius: var(--radius-md);
          font-family: var(--font-body);
          font-weight: 600;
          font-size: 0.8125rem;
          letter-spacing: 0.01em;
          text-decoration: none;
          transition: background 0.2s;
        }
        .new-btn:hover {
          background: var(--accent-bright);
          text-decoration: none;
          color: #0a0d12;
        }

        /* ---- Empty state ---- */
        .empty {
          text-align: center;
          padding: 6rem 0;
        }
        .empty-prompt {
          font-family: var(--font-body);
          font-size: 0.875rem;
          color: var(--text-tertiary);
          margin-bottom: 0.5rem;
        }
        .empty-cta {
          font-family: var(--font-display);
          font-style: italic;
          font-size: 1.25rem;
          color: var(--text-secondary);
          margin-bottom: 2.5rem;
        }

        /* ---- Grid ---- */
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
          gap: 1.25rem;
        }

        /* ---- Card ---- */
        .card {
          background: var(--bg-card);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-lg);
          padding: 2rem;
          transition: border-color 0.3s;
        }
        .card:hover {
          border-color: var(--border-default);
        }
        .card-link {
          display: block;
          color: inherit;
          text-decoration: none;
        }
        .card-link:hover {
          text-decoration: none;
          color: inherit;
        }
        .card-header-right {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .delete-btn {
          background: none;
          border: 1px solid transparent;
          border-radius: var(--radius-md);
          color: var(--text-ghost);
          font-size: 1rem;
          line-height: 1;
          padding: 0.125rem 0.375rem;
          cursor: pointer;
          transition: color 0.2s, border-color 0.2s;
        }
        .delete-btn:hover {
          color: var(--danger, #e55);
          border-color: var(--danger, #e55);
        }
        .delete-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        /* ---- Status badges ---- */
        .status {
          font-family: var(--font-mono);
          font-size: 0.625rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          font-weight: 500;
          padding: 0.1875rem 0.5rem;
          border-radius: 999px;
        }
        .status-pending {
          background: var(--warning-bg);
          color: var(--warning);
        }
        .status-running {
          background: var(--info-bg);
          color: var(--info);
        }
        .status-complete {
          background: var(--success-bg);
          color: var(--success);
        }
        .status-failed {
          background: var(--danger-bg);
          color: var(--danger);
        }

        /* ---- Card content ---- */
        .topic {
          font-family: var(--font-display);
          font-size: 1.125rem;
          font-weight: 400;
          color: var(--text-heading);
          margin-bottom: 0.25rem;
          line-height: 1.35;
        }
        .meta {
          font-size: 0.8125rem;
          color: var(--text-tertiary);
          letter-spacing: 0.01em;
        }

        .stats-row {
          display: flex;
          gap: 2rem;
          margin-top: 1.5rem;
          padding-top: 1.25rem;
          border-top: 1px solid var(--border-subtle);
        }
        .stat {
          display: flex;
          flex-direction: column;
          gap: 0.1875rem;
        }
        .stat-val {
          font-family: var(--font-mono);
          font-size: 1rem;
          font-weight: 600;
          color: var(--text-heading);
        }
        .stat-lbl {
          font-family: var(--font-mono);
          font-size: 0.5625rem;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--text-tertiary);
        }

        .date {
          font-family: var(--font-mono);
          font-size: 0.625rem;
          color: var(--text-ghost);
          letter-spacing: 0.02em;
        }
      `}</style>
    </main>
  );
}
