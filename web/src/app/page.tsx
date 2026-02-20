import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <nav>
        <div className="logo">Epistemix</div>
        <div className="nav-links">
          <Link href="/auth/login">Sign In</Link>
        </div>
      </nav>

      <section className="hero">
        <h1>
          Find what you
          <br />
          <span className="gradient">don't know you're missing</span>
        </h1>
        <p className="subtitle">
          Epistemix audits research topics to detect unknown unknowns &mdash;
          missing languages, absent disciplines, overlooked scholars, and
          unexamined theories that traditional searches miss.
        </p>
        <div className="cta">
          <Link href="/audit/new" className="btn primary">
            Start an Audit
          </Link>
          <Link href="/dashboard" className="btn secondary">
            Dashboard
          </Link>
        </div>
      </section>

      <section className="features">
        <div className="feature">
          <div className="feature-icon">7</div>
          <h3>Meta-Axioms</h3>
          <p>
            Seven structural rules about how knowledge works drive predictions
            about what should exist.
          </p>
        </div>
        <div className="feature">
          <div className="feature-icon">2</div>
          <h3>Dual Agents</h3>
          <p>
            Two agents with different weightings independently audit. Where they
            disagree, you have a proven blind spot.
          </p>
        </div>
        <div className="feature">
          <div className="feature-icon">N</div>
          <h3>Multilingual</h3>
          <p>
            Searches across language barriers. A monolingual search inherently
            misses perspectives.
          </p>
        </div>
      </section>

      <style jsx>{`
        main {
          max-width: 1120px;
          margin: 0 auto;
          padding: 0 1.5rem;
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
          letter-spacing: -0.025em;
        }
        .nav-links {
          display: flex;
          gap: 1.5rem;
        }
        .hero {
          text-align: center;
          padding: 6rem 0 4rem;
        }
        h1 {
          font-size: 3.5rem;
          font-weight: 800;
          line-height: 1.1;
          letter-spacing: -0.03em;
          color: #f1f5f9;
        }
        .gradient {
          background: linear-gradient(135deg, #6366f1, #8b5cf6, #f97316);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .subtitle {
          max-width: 600px;
          margin: 1.5rem auto 2.5rem;
          font-size: 1.125rem;
          line-height: 1.6;
          color: #94a3b8;
        }
        .cta {
          display: flex;
          gap: 1rem;
          justify-content: center;
        }
        .btn {
          padding: 0.75rem 2rem;
          border-radius: 0.5rem;
          font-weight: 600;
          font-size: 1rem;
          transition: all 0.2s;
        }
        .btn.primary {
          background: #6366f1;
          color: white;
        }
        .btn.primary:hover {
          background: #4f46e5;
          text-decoration: none;
        }
        .btn.secondary {
          background: #1e293b;
          color: #e2e8f0;
          border: 1px solid #334155;
        }
        .btn.secondary:hover {
          background: #334155;
          text-decoration: none;
        }
        .features {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 2rem;
          padding: 4rem 0 6rem;
        }
        .feature {
          background: #0f172a;
          border: 1px solid #1e293b;
          border-radius: 0.75rem;
          padding: 2rem;
          text-align: center;
        }
        .feature-icon {
          width: 48px;
          height: 48px;
          margin: 0 auto 1rem;
          background: rgba(99, 102, 241, 0.15);
          color: #6366f1;
          border-radius: 0.75rem;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
          font-weight: 800;
        }
        .feature h3 {
          color: #f1f5f9;
          font-size: 1.125rem;
          margin-bottom: 0.5rem;
        }
        .feature p {
          color: #94a3b8;
          font-size: 0.875rem;
          line-height: 1.5;
        }
        @media (max-width: 768px) {
          h1 { font-size: 2.25rem; }
          .features { grid-template-columns: 1fr; }
        }
      `}</style>
    </main>
  );
}
