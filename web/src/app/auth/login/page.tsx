"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const router = useRouter();
  const { signInWithEmail, signUpWithEmail, signInWithGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const { error } = isSignUp
      ? await signUpWithEmail(email, password)
      : await signInWithEmail(email, password);

    if (error) {
      setError(error.message);
      setLoading(false);
    } else {
      router.push("/dashboard");
    }
  }

  return (
    <main>
      <div className="container">
        <h1>Epistemix</h1>
        <p className="subtitle">
          {isSignUp ? "Create an account" : "Sign in to your account"}
        </p>

        <button className="google-btn" onClick={signInWithGoogle}>
          Continue with Google
        </button>

        <div className="divider">
          <span>or</span>
        </div>

        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading}>
            {loading ? "Loading..." : isSignUp ? "Sign Up" : "Sign In"}
          </button>
        </form>

        <p className="toggle">
          {isSignUp ? "Already have an account?" : "Don\u2019t have an account?"}{" "}
          <button
            className="link"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError(null);
            }}
          >
            {isSignUp ? "Sign in" : "Sign up"}
          </button>
        </p>
      </div>

      <style jsx>{`
        main {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
        }
        .container {
          width: 100%;
          max-width: 360px;
        }
        h1 {
          text-align: center;
          font-family: var(--font-display);
          font-size: 2rem;
          font-weight: 400;
          color: var(--text-heading);
          margin: 0 0 0.375rem;
        }
        .subtitle {
          text-align: center;
          font-family: var(--font-body);
          font-size: 0.875rem;
          color: var(--text-secondary);
          margin: 0 0 2.5rem;
        }
        .google-btn {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid var(--border-default);
          border-radius: var(--radius-md);
          background: transparent;
          color: var(--text-primary);
          font-family: var(--font-body);
          font-size: 0.875rem;
          cursor: pointer;
          transition: border-color 0.2s;
        }
        .google-btn:hover {
          border-color: var(--accent-border);
        }
        .divider {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin: 1.75rem 0;
          color: var(--text-ghost);
          font-family: var(--font-mono);
          font-size: 0.625rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .divider::before,
        .divider::after {
          content: "";
          flex: 1;
          height: 1px;
          background: var(--border-subtle);
        }
        form {
          display: flex;
          flex-direction: column;
          gap: 0.875rem;
        }
        input {
          padding: 0.8125rem 0.875rem;
          border: 1px solid var(--border-default);
          border-radius: var(--radius-sm);
          background: transparent;
          color: var(--text-heading);
          font-family: var(--font-body);
          font-size: 0.875rem;
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        input::placeholder {
          color: var(--text-tertiary);
        }
        input:focus {
          outline: none;
          border-color: var(--accent);
          box-shadow: 0 0 0 2px var(--accent-bg);
        }
        button[type="submit"] {
          width: 100%;
          padding: 0.8125rem;
          margin-top: 0.25rem;
          border: none;
          border-radius: var(--radius-md);
          background: var(--accent);
          color: var(--bg-page);
          font-family: var(--font-body);
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.2s;
        }
        button[type="submit"]:hover:not(:disabled) {
          opacity: 0.9;
        }
        button[type="submit"]:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        .error {
          color: var(--danger);
          font-size: 0.75rem;
          margin: 0;
        }
        .toggle {
          text-align: center;
          margin-top: 2rem;
          font-size: 0.75rem;
          color: var(--text-tertiary);
        }
        .link {
          background: none;
          border: none;
          color: var(--accent);
          cursor: pointer;
          font-size: 0.75rem;
          padding: 0;
          font-family: var(--font-body);
        }
        .link:hover {
          color: var(--accent-bright);
        }
      `}</style>
    </main>
  );
}
