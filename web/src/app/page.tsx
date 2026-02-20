"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase";
import styles from "./page.module.css";

const ALLOWED_EMAILS = [
  "francesco3.rinaldi@gmail.com",
  "catenacci.fabrizio@hotmail.it",
];

export default function HomePage() {
  const router = useRouter();
  const supabase = createClient();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [signingIn, setSigningIn] = useState(false);

  useEffect(() => {
    async function checkUser() {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (user) {
        if (ALLOWED_EMAILS.includes(user.email ?? "")) {
          router.push("/dashboard");
          return;
        } else {
          await supabase.auth.signOut();
          setError("Access restricted. Your email is not authorized.");
        }
      }
      setLoading(false);
    }

    checkUser();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      if (session?.user) {
        if (ALLOWED_EMAILS.includes(session.user.email ?? "")) {
          router.push("/dashboard");
        } else {
          await supabase.auth.signOut();
          setError("Access restricted. Your email is not authorized.");
        }
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  async function handleGoogleSignIn() {
    setSigningIn(true);
    setError(null);
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) {
      setError(error.message);
      setSigningIn(false);
    }
  }

  if (loading) {
    return (
      <main className={styles.main}>
        <div className={styles.loading}>loading</div>
      </main>
    );
  }

  return (
    <main className={styles.main}>
      {/* Navigation */}
      <nav className={styles.nav}>
        <span className={styles.logo}>Epistemix</span>
        <a
          href="https://github.com/francescorinaldi/epistemix"
          className={styles.navLink}
          target="_blank"
          rel="noopener noreferrer"
        >
          GitHub
        </a>
      </nav>

      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.eyebrow}>Epistemic Audit Framework</div>
        <h1 className={styles.title}>
          Map the boundaries
          <br />
          of what is known
          <span className={styles.titleAccent}>&mdash; and what isn&apos;t.</span>
        </h1>
        <p className={styles.subtitle}>
          Epistemix predicts what knowledge should exist about a research topic,
          then verifies whether it does. The gap between expectation and
          reality reveals the blind spots no one is looking for.
        </p>

        <div className={styles.ctaWrap}>
          <button
            className={styles.googleBtn}
            onClick={handleGoogleSignIn}
            disabled={signingIn}
          >
            <svg viewBox="0 0 24 24" width="18" height="18" className={styles.googleIcon}>
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            {signingIn ? "Redirecting..." : "Continue with Google"}
          </button>
          {error && <p className={styles.error}>{error}</p>}
        </div>
      </section>

      {/* Divider */}
      <div className={styles.divider}>
        <div className={styles.dividerLine} />
      </div>

      {/* How it works */}
      <section className={styles.howSection}>
        <div className={styles.sectionLabel}>How it works</div>
        <h2 className={styles.sectionTitle}>Three passes, converging on the unknown</h2>
        <div className={styles.steps}>
          <div className={styles.step}>
            <div className={styles.stepNumber}>01</div>
            <div className={styles.stepTitle}>Predict</div>
            <p className={styles.stepDesc}>
              Seven meta-axioms about how academic knowledge is structured
              generate testable hypotheses &mdash; postulates about what languages,
              institutions, theories, and disciplines should be present.
            </p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>02</div>
            <div className={styles.stepTitle}>Search</div>
            <p className={styles.stepDesc}>
              Multilingual queries reach across language barriers.
              A monolingual search inherently misses perspectives &mdash; Epistemix
              searches in English, Greek, French, German, Italian, and more.
            </p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>03</div>
            <div className={styles.stepTitle}>Detect</div>
            <p className={styles.stepDesc}>
              Findings are compared against postulates. Gaps become anomalies:
              missing disciplines, citation islands, echo chambers.
              Coverage is always a lower bound &mdash; the map is never complete.
            </p>
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className={styles.divider}>
        <div className={styles.dividerLine} />
      </div>

      {/* Dual agent */}
      <section className={styles.agentSection}>
        <div className={styles.sectionLabel} style={{ marginTop: '3rem' }}>Dual-agent verification</div>
        <h2 className={styles.sectionTitle}>Two perspectives. One truth.</h2>
        <div className={styles.agentCard}>
          <div className={styles.agentText}>
            <h2>Where they disagree,<br />you have a blind spot</h2>
            <p>
              Agent &alpha; focuses on institutional structure &mdash; languages,
              institutions, citation schools, publication channels. Agent &beta;
              focuses on theoretical substance &mdash; competing theories,
              disciplinary breadth, temporal evolution.
            </p>
            <p>
              An independent arbiter compares their reports. Agreements
              strengthen confidence. Disagreements become <em>known unknowns</em>&nbsp;&mdash;
              the most valuable output of the audit.
            </p>
            <div className={styles.agentFormula}>
              coverage = min(&alpha;, &beta;)&nbsp;&nbsp;&middot;&nbsp;&nbsp;blindness gap = max(&alpha;,&beta;) - min(&alpha;,&beta;)
            </div>
          </div>
          <div className={styles.agentVisual}>
            <div className={styles.agentBar}>
              <span className={styles.agentLabel}>Agent &alpha;</span>
              <div className={styles.barTrack}>
                <div className={styles.barFillAlpha} />
              </div>
            </div>
            <div className={styles.agentBar}>
              <span className={styles.agentLabel}>Agent &beta;</span>
              <div className={styles.barTrack}>
                <div className={styles.barFillBeta} />
              </div>
            </div>
            <div className={styles.agentDivider}>disagreement zone</div>
            <div className={styles.agentBar}>
              <span className={styles.agentLabel}>Gap</span>
              <div className={styles.barTrack}>
                <div className={styles.barFillGap} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <span className={styles.footerText}>Epistemix v0.2.0</span>
        <span className={styles.footerText}>MIT License</span>
      </footer>
    </main>
  );
}
