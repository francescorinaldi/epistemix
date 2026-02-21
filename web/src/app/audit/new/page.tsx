"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import AuditForm from "@/components/AuditForm";

export default function NewAuditPage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <>
        <div className="loading">Loading...</div>
        <style jsx>{`
          .loading {
            text-align: center;
            padding: 4rem;
            font-family: var(--font-mono);
            font-size: 0.8125rem;
            color: var(--text-tertiary);
          }
        `}</style>
      </>
    );
  }

  return (
    <main>
      <nav>
        <Link href="/dashboard" className="back">
          &larr; Dashboard
        </Link>
      </nav>

      <div className="content">
        <h1>New Epistemic Audit</h1>
        <p className="subtitle">
          Define your research topic. Epistemix will predict what knowledge
          should exist and verify whether it does.
        </p>
        <AuditForm />
      </div>

      <style jsx>{`
        main {
          max-width: 600px;
          margin: 0 auto;
          padding: 0 2rem 4rem;
        }
        nav {
          padding: 2rem 0;
        }
        nav :global(.back) {
          font-family: var(--font-mono);
          font-size: 0.6875rem;
          color: var(--text-tertiary);
          text-decoration: none;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          transition: color 0.2s;
        }
        nav :global(.back:hover) {
          color: var(--text-primary);
        }
        .content {
          padding-top: 3rem;
        }
        h1 {
          font-family: var(--font-display);
          font-size: 2rem;
          font-weight: 400;
          text-align: center;
          color: var(--text-heading);
          margin: 0 0 0.5rem;
        }
        .subtitle {
          text-align: center;
          color: var(--text-secondary);
          max-width: 400px;
          margin: 0 auto 3.5rem;
          font-family: var(--font-body);
          font-size: 0.875rem;
          line-height: 1.7;
        }
      `}</style>
    </main>
  );
}
