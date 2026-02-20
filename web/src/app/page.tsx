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
        <div className={styles.loading}>Loading...</div>
      </main>
    );
  }

  return (
    <main className={styles.main}>
      <section className={styles.hero}>
        <div className={styles.logoMark}>E</div>
        <h1>
          Find what you
          <br />
          <span className={styles.gradient}>don&apos;t know you&apos;re missing</span>
        </h1>
        <p className={styles.subtitle}>
          Epistemix audits research topics to detect unknown unknowns &mdash;
          missing languages, absent disciplines, overlooked scholars, and
          unexamined theories that traditional searches miss.
        </p>

        <button
          className={styles.googleBtn}
          onClick={handleGoogleSignIn}
          disabled={signingIn}
        >
          <svg viewBox="0 0 24 24" width="20" height="20" className={styles.googleIcon}>
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
      </section>

      <section className={styles.features}>
        <div className={styles.feature}>
          <div className={styles.featureIcon}>7</div>
          <h3 className={styles.featureTitle}>Meta-Axioms</h3>
          <p className={styles.featureDesc}>
            Seven structural rules about how knowledge works drive predictions
            about what should exist.
          </p>
        </div>
        <div className={styles.feature}>
          <div className={styles.featureIcon}>2</div>
          <h3 className={styles.featureTitle}>Dual Agents</h3>
          <p className={styles.featureDesc}>
            Two agents with different weightings independently audit. Where they
            disagree, you have a proven blind spot.
          </p>
        </div>
        <div className={styles.feature}>
          <div className={styles.featureIcon}>N</div>
          <h3 className={styles.featureTitle}>Multilingual</h3>
          <p className={styles.featureDesc}>
            Searches across language barriers. A monolingual search inherently
            misses perspectives.
          </p>
        </div>
      </section>
    </main>
  );
}
