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

  async function handleSubmit(e: React.FormEvent) {
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
          {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
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
          max-width: 380px;
        }
        h1 {
          text-align: center;
          font-size: 2rem;
          font-weight: 800;
          color: #6366f1;
          margin-bottom: 0.5rem;
        }
        .subtitle {
          text-align: center;
          color: #94a3b8;
          margin-bottom: 2rem;
        }
        .google-btn {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #334155;
          border-radius: 0.5rem;
          background: #1e293b;
          color: #e2e8f0;
          font-size: 0.9375rem;
          cursor: pointer;
          transition: background 0.2s;
        }
        .google-btn:hover {
          background: #334155;
        }
        .divider {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin: 1.5rem 0;
          color: #64748b;
          font-size: 0.8125rem;
        }
        .divider::before,
        .divider::after {
          content: "";
          flex: 1;
          height: 1px;
          background: #334155;
        }
        form {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        input {
          padding: 0.625rem 0.75rem;
          border: 1px solid #334155;
          border-radius: 0.5rem;
          background: #1e293b;
          color: #f1f5f9;
          font-size: 0.9375rem;
        }
        input:focus {
          outline: none;
          border-color: #6366f1;
        }
        button[type="submit"] {
          padding: 0.75rem;
          border: none;
          border-radius: 0.5rem;
          background: #6366f1;
          color: white;
          font-weight: 600;
          cursor: pointer;
        }
        button[type="submit"]:hover:not(:disabled) {
          background: #4f46e5;
        }
        button:disabled {
          opacity: 0.5;
        }
        .error {
          color: #f87171;
          font-size: 0.875rem;
        }
        .toggle {
          text-align: center;
          margin-top: 1.5rem;
          color: #94a3b8;
          font-size: 0.875rem;
        }
        .link {
          background: none;
          border: none;
          color: #6366f1;
          cursor: pointer;
          font-size: 0.875rem;
        }
      `}</style>
    </main>
  );
}
