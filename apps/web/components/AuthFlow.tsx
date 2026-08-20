"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, FlaskConical } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { api } from "@/lib/api";

type Mode =
  "login" | "register" | "forgot" | "reset" | "verify" | "unsubscribe";

const credentials = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(12, "Use at least 12 characters."),
});

export default function AuthFlow({ mode }: { mode: Mode }) {
  const router = useRouter();
  const search = useSearchParams();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const form = useForm<z.infer<typeof credentials>>({
    resolver: zodResolver(credentials),
    defaultValues: { email: "", password: "" },
  });

  useEffect(() => {
    async function consume() {
      const token = search.get("token");
      if (!token || !["verify", "unsubscribe"].includes(mode)) return;
      setBusy(true);
      try {
        const result = await api<{ message: string }>(
          mode === "verify"
            ? "/auth/verify-email"
            : `/email/unsubscribe?token=${encodeURIComponent(token)}`,
          {
            method: "POST",
            body: mode === "verify" ? JSON.stringify({ token }) : undefined,
          },
        );
        setMessage(result.message);
      } catch (reason) {
        setError(
          reason instanceof Error
            ? reason.message
            : "The link could not be used.",
        );
      } finally {
        setBusy(false);
      }
    }
    void consume();
  }, [mode, search]);

  async function submit(values: z.infer<typeof credentials>) {
    setBusy(true);
    setError("");
    try {
      if (mode === "login") {
        const result = await api<{
          user: { deletion_requested: boolean };
        }>("/auth/login", {
          method: "POST",
          body: JSON.stringify(values),
        });
        router.push(
          result.user.deletion_requested ? "/account-deletion" : "/dashboard",
        );
      } else if (mode === "register") {
        const result = await api<{ message: string }>("/auth/register", {
          method: "POST",
          body: JSON.stringify({
            ...values,
            anonymous_id: localStorage.getItem("equitylens_anonymous_id"),
          }),
        });
        setMessage(result.message);
      } else if (mode === "forgot") {
        const result = await api<{ message: string }>("/auth/forgot-password", {
          method: "POST",
          body: JSON.stringify({ email: values.email }),
        });
        setMessage(result.message);
      } else if (mode === "reset") {
        const token = search.get("token");
        const result = await api<{ message: string }>("/auth/reset-password", {
          method: "POST",
          body: JSON.stringify({ token, password: values.password }),
        });
        setMessage(result.message);
      }
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The request could not be completed.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function demoLogin() {
    setBusy(true);
    setError("");
    try {
      await api("/auth/demo-login", {
        method: "POST",
        body: JSON.stringify({ role: "user" }),
      });
      router.push("/dashboard");
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Demo login is unavailable.",
      );
    } finally {
      setBusy(false);
    }
  }

  const copy = {
    login: [
      "Welcome back",
      "Continue your research without losing the assumptions.",
    ],
    register: [
      "Build your research list",
      "Verify your email, choose three stocks, and inspect every factor.",
    ],
    forgot: [
      "Reset access safely",
      "We use the same response whether or not an account exists.",
    ],
    reset: [
      "Choose a new password",
      "The link expires after one use and older sessions are revoked.",
    ],
    verify: ["Verify your email", "This unlocks protected research workflows."],
    unsubscribe: [
      "Digest preferences",
      "Security messages remain separate from optional lifecycle email.",
    ],
  }[mode];

  const showEmail = ["login", "register", "forgot"].includes(mode);
  const showPassword = ["login", "register", "reset"].includes(mode);

  return (
    <main className="auth-layout">
      <section className="auth-copy">
        <span className="eyebrow" style={{ color: "var(--lime)" }}>
          Account security
        </span>
        <h1>{copy[0]}</h1>
        <p className="lead" style={{ color: "#b9c9c1" }}>
          {copy[1]}
        </p>
        <p style={{ marginTop: "auto", color: "#91a79d", fontSize: ".82rem" }}>
          For education and research only. Not investment advice.
        </p>
      </section>
      <section className="auth-panel">
        <div className="auth-card card">
          <span className="eyebrow">EquityLens</span>
          <h2 style={{ fontSize: "2rem" }}>{copy[0]}</h2>
          {message ? (
            <div className="form-grid">
              <p className="form-message">{message}</p>
              <Link
                className="button"
                href={mode === "verify" ? "/onboarding" : "/login"}
              >
                Continue <ArrowRight size={17} />
              </Link>
            </div>
          ) : ["verify", "unsubscribe"].includes(mode) ? (
            <div className="loading-state">
              <p>
                {busy
                  ? "Validating the signed link…"
                  : error || "A token is required."}
              </p>
            </div>
          ) : (
            <form className="form-grid" onSubmit={form.handleSubmit(submit)}>
              {showEmail && (
                <label>
                  Email
                  <input
                    type="email"
                    autoComplete="email"
                    {...form.register("email")}
                  />
                  {form.formState.errors.email && (
                    <span className="negative">
                      {form.formState.errors.email.message}
                    </span>
                  )}
                </label>
              )}
              {showPassword && (
                <label>
                  {mode === "reset" ? "New password" : "Password"}
                  <input
                    type="password"
                    autoComplete={
                      mode === "login" ? "current-password" : "new-password"
                    }
                    {...form.register("password")}
                  />
                  {form.formState.errors.password && (
                    <span className="negative">
                      {form.formState.errors.password.message}
                    </span>
                  )}
                </label>
              )}
              {error && <p className="form-message error">{error}</p>}
              <button className="button" disabled={busy}>
                {busy
                  ? "Working…"
                  : mode === "login"
                    ? "Sign in"
                    : mode === "register"
                      ? "Create account"
                      : mode === "forgot"
                        ? "Send reset instructions"
                        : "Update password"}
              </button>
              {mode === "login" && (
                <>
                  <button
                    type="button"
                    className="button secondary"
                    onClick={demoLogin}
                    disabled={busy}
                  >
                    <FlaskConical size={17} /> One-click demo login
                  </button>
                  <Link href="/forgot-password" className="muted">
                    Forgot password?
                  </Link>
                  <p className="muted">
                    New here?{" "}
                    <Link href="/register" className="positive">
                      Create an account
                    </Link>
                    .
                  </p>
                </>
              )}
              {mode === "register" && (
                <p className="muted">
                  Already registered?{" "}
                  <Link href="/login" className="positive">
                    Sign in
                  </Link>
                  .
                </p>
              )}
            </form>
          )}
        </div>
      </section>
    </main>
  );
}
