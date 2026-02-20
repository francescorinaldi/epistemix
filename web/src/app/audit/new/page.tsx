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
    return <div className="loading">Loading...</div>;
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
          max-width: 640px;
          margin: 0 auto;
          padding: 0 1.5rem 4rem;
        }
        nav {
          padding: 1.5rem 0;
        }
        .back {
          color: #94a3b8;
          font-size: 0.875rem;
        }
        .content {
          padding-top: 2rem;
        }
        h1 {
          font-size: 1.75rem;
          font-weight: 700;
          text-align: center;
          margin-bottom: 0.5rem;
        }
        .subtitle {
          text-align: center;
          color: #94a3b8;
          max-width: 440px;
          margin: 0 auto 2.5rem;
          font-size: 0.9375rem;
          line-height: 1.5;
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
