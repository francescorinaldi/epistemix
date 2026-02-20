"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { createClient } from "@/lib/supabase";
import type { Audit } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  pending: "#f59e0b",
  running: "#6366f1",
  complete: "#10b981",
  failed: "#f87171",
};

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
    return <div className="loading">Loading...</div>;
  }

  return (
    <main>
      <nav>
        <Link href="/" className="logo">Epistemix</Link>
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
          <p>No audits yet. Start your first epistemic audit.</p>
          <Link href="/audit/new" className="new-btn">
            Start Audit
          </Link>
        </div>
      ) : (
        <div className="grid">
          {audits.map((audit) => {
            const lastCoverage =
              audit.coverage_history.length > 0
                ? audit.coverage_history[audit.coverage_history.length - 1]
                : null;
            return (
              <Link
                key={audit.id}
                href={`/audit/${audit.id}`}
                className="card"
              >
                <div className="card-header">
                  <span
                    className="status"
                    style={{ color: STATUS_COLORS[audit.status] }}
                  >
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
                      {audit.findings?.length ?? 0}
                    </span>
                    <span className="stat-lbl">Findings</span>
                  </div>
                  <div className="stat">
                    <span className="stat-val">
                      {audit.anomalies?.length ?? 0}
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
          max-width: 1120px;
          margin: 0 auto;
          padding: 0 1.5rem 4rem;
        }
        nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem 0;
        }
        .logo {
          font-size: 1.25rem;
          font-weight: 800;
          color: #6366f1;
        }
        .nav-right {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        .plan-badge {
          font-size: 0.6875rem;
          text-transform: uppercase;
          font-weight: 700;
          padding: 0.125rem 0.5rem;
          border-radius: 999px;
          background: rgba(99, 102, 241, 0.15);
          color: #a5b4fc;
        }
        .usage {
          color: #64748b;
          font-size: 0.8125rem;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin: 2rem 0 1.5rem;
        }
        h1 {
          font-size: 1.75rem;
          font-weight: 700;
        }
        .new-btn {
          padding: 0.625rem 1.25rem;
          background: #6366f1;
          color: white;
          border-radius: 0.5rem;
          font-weight: 600;
          font-size: 0.875rem;
          transition: background 0.2s;
        }
        .new-btn:hover {
          background: #4f46e5;
          text-decoration: none;
        }
        .empty {
          text-align: center;
          padding: 4rem 0;
          color: #64748b;
        }
        .empty p {
          margin-bottom: 1.5rem;
        }
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 1rem;
        }
        .card {
          background: #0f172a;
          border: 1px solid #1e293b;
          border-radius: 0.75rem;
          padding: 1.25rem;
          transition: border-color 0.2s;
          color: inherit;
          display: block;
        }
        .card:hover {
          border-color: #6366f1;
          text-decoration: none;
        }
        .card-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.75rem;
        }
        .status {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
        }
        .date {
          font-size: 0.75rem;
          color: #64748b;
        }
        .topic {
          font-size: 1.0625rem;
          font-weight: 600;
          color: #f1f5f9;
          margin-bottom: 0.25rem;
        }
        .meta {
          font-size: 0.8125rem;
          color: #64748b;
          margin-bottom: 1rem;
        }
        .stats-row {
          display: flex;
          gap: 1.5rem;
        }
        .stat {
          display: flex;
          flex-direction: column;
        }
        .stat-val {
          font-size: 1.125rem;
          font-weight: 700;
          color: #e2e8f0;
        }
        .stat-lbl {
          font-size: 0.6875rem;
          color: #64748b;
        }
        .loading {
          text-align: center;
          padding: 4rem;
          color: #64748b;
        }
      `}</style>
    </main>
  );
}
