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
            font-size: 0.8125rem;
            color: var(--text-tertiary);
            letter-spacing: 0.12em;
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
              <Link
                key={audit.id}
                href={`/audit/${audit.id}`}
                className="card"
              >
                <div className="card-header">
                  <span className={`status status-${audit.status}`}>
                    {audit.status}
                  </span>
                  <span className="date">
                    {new Date(audit.created_at).toLocaleDateString()}
                  </span>
                </div>
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
            );
          })}
        </div>
      )}

      <style jsx>{`
        main {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 2rem 4rem;
          position: relative;
          z-index: 1;
        }

        /* ---- Nav ---- */
        nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.75rem 0;
          border-bottom: 1px solid var(--border-subtle);
          margin-bottom: 0.5rem;
        }
        .logo {
          font-family: var(--font-body);
          font-size: 0.8125rem;
          font-weight: 600;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--text-secondary);
          text-decoration: none;
          transition: color 0.2s;
        }
        .logo:hover {
          color: var(--text-heading);
          text-decoration: none;
        }
        .nav-right {
          display: flex;
          align-items: center;
          gap: 1rem;
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
          font-size: 0.75rem;
          color: var(--text-tertiary);
        }

        /* ---- Header ---- */
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin: 2.5rem 0 1.75rem;
        }
        h1 {
          font-family: var(--font-display);
          font-size: 2rem;
          font-weight: 400;
          color: var(--text-heading);
        }
        .new-btn {
          display: inline-flex;
          align-items: center;
          padding: 0.625rem 1.25rem;
          background: var(--accent);
          color: #0b0e15;
          border-radius: var(--radius-md);
          font-family: var(--font-body);
          font-weight: 600;
          font-size: 0.875rem;
          text-decoration: none;
          transition: filter 0.2s, transform 0.2s;
        }
        .new-btn:hover {
          filter: brightness(1.1);
          transform: translateY(-1px);
          text-decoration: none;
          color: #0b0e15;
        }

        /* ---- Empty state ---- */
        .empty {
          text-align: center;
          padding: 5rem 0;
          color: var(--text-tertiary);
        }
        .empty-prompt {
          font-family: var(--font-body);
          font-size: 0.9375rem;
          color: var(--text-tertiary);
          margin-bottom: 0.5rem;
        }
        .empty-cta {
          font-family: var(--font-display);
          font-style: italic;
          font-size: 1.125rem;
          color: var(--text-secondary);
          margin-bottom: 2rem;
        }

        /* ---- Grid ---- */
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
          gap: 1rem;
        }

        /* ---- Card ---- */
        .card {
          background: var(--bg-card);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-lg);
          padding: 1.5rem;
          display: block;
          color: inherit;
          text-decoration: none;
          transition: border-color 0.25s, box-shadow 0.25s, transform 0.25s;
        }
        .card:hover {
          border-color: var(--accent-border);
          box-shadow: var(--shadow-card);
          transform: translateY(-2px);
          text-decoration: none;
          color: inherit;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
        }

        /* ---- Status badges ---- */
        .status {
          font-family: var(--font-mono);
          font-size: 0.6875rem;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          font-weight: 500;
          padding: 0.125rem 0.625rem;
          border-radius: 999px;
        }
        .status-pending {
          background: var(--warning-bg);
          border: 1px solid var(--warning-border);
          color: var(--warning);
        }
        .status-running {
          background: var(--info-bg);
          border: 1px solid var(--info-border);
          color: var(--info);
        }
        .status-complete {
          background: var(--success-bg);
          border: 1px solid var(--success-border);
          color: var(--success);
        }
        .status-failed {
          background: var(--danger-bg);
          border: 1px solid var(--danger-border);
          color: var(--danger);
        }

        /* ---- Card content ---- */
        .topic {
          font-family: var(--font-display);
          font-size: 1.125rem;
          font-weight: 400;
          color: var(--text-heading);
          margin-bottom: 0.25rem;
          line-height: 1.3;
        }
        .meta {
          font-size: 0.8125rem;
          color: var(--text-tertiary);
        }

        .stats-row {
          display: flex;
          gap: 1.5rem;
          margin-top: 1.25rem;
          padding-top: 1rem;
          border-top: 1px solid var(--border-subtle);
        }
        .stat {
          display: flex;
          flex-direction: column;
          gap: 0.125rem;
        }
        .stat-val {
          font-family: var(--font-mono);
          font-size: 1.125rem;
          font-weight: 700;
          color: var(--text-heading);
        }
        .stat-lbl {
          font-family: var(--font-mono);
          font-size: 0.625rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--text-tertiary);
        }

        .date {
          font-family: var(--font-mono);
          font-size: 0.6875rem;
          color: var(--text-ghost);
        }
      `}</style>
    </main>
  );
}
