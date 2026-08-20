"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import Disclosure from "@/components/Disclosure";
import { api } from "@/lib/api";
import { PageHead, QueryState } from "./Shared";

type SettingsData = {
  theme: string;
  model_version: string;
  email: string;
  verified: boolean;
  disclosure: string;
};

export default function SettingsPanel() {
  const query = useQuery({
    queryKey: ["settings"],
    queryFn: () => api<SettingsData>("/settings"),
  });
  const prefs = useQuery({
    queryKey: ["email-preferences"],
    queryFn: () =>
      api<{ weekly_digest: boolean; analytics_enabled: boolean }>(
        "/email/preferences",
      ),
  });
  const [message, setMessage] = useState("");
  const [password, setPassword] = useState("");
  const [deletionPending, setDeletionPending] = useState(false);
  const [busy, setBusy] = useState(false);

  async function updatePrefs(
    name: "weekly_digest" | "analytics_enabled",
    value: boolean,
  ) {
    const current = prefs.data ?? {
      weekly_digest: false,
      analytics_enabled: true,
    };
    await api("/email/preferences", {
      method: "PUT",
      body: JSON.stringify({ ...current, [name]: value }),
    });
    setMessage("Preferences saved.");
    await prefs.refetch();
  }

  async function exportData() {
    const data = await api<Record<string, unknown>>("/account/export");
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "equitylens-export.json";
    anchor.click();
    URL.revokeObjectURL(url);
    setMessage("Export downloaded.");
  }

  async function requestDeletion() {
    if (!password) {
      setMessage("Enter your current password to continue.");
      return;
    }
    if (
      !window.confirm("Schedule account deletion and revoke active sessions?")
    )
      return;
    setBusy(true);
    setMessage("");
    try {
      const result = await api<{ grace_days: number }>(
        "/account/delete-request",
        {
          method: "POST",
          body: JSON.stringify({ password }),
        },
      );
      setPassword("");
      setDeletionPending(true);
      setMessage(
        `Deletion scheduled. You have ${result.grace_days} days to cancel.`,
      );
    } catch (reason) {
      setMessage(
        reason instanceof Error
          ? reason.message
          : "Deletion could not be scheduled.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function cancelDeletion() {
    setBusy(true);
    setMessage("");
    try {
      await api("/account/delete-cancel", { method: "POST" });
      setDeletionPending(false);
      setMessage("Deletion request cancelled.");
    } catch (reason) {
      setMessage(
        reason instanceof Error ? reason.message : "Cancellation failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead
        eyebrow="Account controls"
        title="Settings"
        copy="Privacy, lifecycle email, display, and version context in one place."
      />
      <QueryState
        loading={query.isLoading || prefs.isLoading}
        error={query.error ?? prefs.error}
      />
      {query.data && prefs.data && (
        <div className="content-grid">
          <section className="card form-grid">
            <div>
              <span className="metric-label">Account email</span>
              <strong>{query.data.email}</strong>
              <p className="muted">
                {query.data.verified ? "Verified" : "Verification required"}
              </p>
            </div>
            <div>
              <span className="metric-label">Research model</span>
              <strong>{query.data.model_version}</strong>
              <p className="muted">
                Saved snapshots and backtests retain their engine version.
              </p>
            </div>
            <label style={{ display: "flex", alignItems: "center" }}>
              <input
                type="checkbox"
                style={{ width: 20, minHeight: 20 }}
                checked={prefs.data.weekly_digest}
                onChange={(event) =>
                  void updatePrefs("weekly_digest", event.target.checked)
                }
              />{" "}
              Weekly watchlist digest (explicit opt-in)
            </label>
            <label style={{ display: "flex", alignItems: "center" }}>
              <input
                type="checkbox"
                style={{ width: 20, minHeight: 20 }}
                checked={prefs.data.analytics_enabled}
                onChange={(event) =>
                  void updatePrefs("analytics_enabled", event.target.checked)
                }
              />{" "}
              Privacy-conscious product analytics
            </label>
            {message && (
              <p className="form-message" role="status">
                {message}
              </p>
            )}
          </section>
          <aside className="card form-grid">
            <h2>Your data</h2>
            <p className="muted">
              Download profile, watchlist, saved configurations, simulated
              ledger, preferences, referrals, and feedback as JSON.
            </p>
            <button className="button secondary" onClick={exportData}>
              Download my data
            </button>
            <h3>Deletion requests</h3>
            <p className="muted">
              Password reauthentication is required. A request immediately
              disables lifecycle email and revokes refresh sessions, followed by
              a reversible grace period.
            </p>
            {deletionPending ? (
              <button
                className="button"
                disabled={busy}
                onClick={cancelDeletion}
              >
                Cancel deletion request
              </button>
            ) : (
              <>
                <label>
                  Current password
                  <input
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                </label>
                <button
                  className="button danger"
                  disabled={busy}
                  onClick={requestDeletion}
                >
                  {busy ? "Schedulingâ€¦" : "Schedule account deletion"}
                </button>
              </>
            )}
          </aside>
        </div>
      )}
      <div style={{ marginTop: "1rem" }}>
        <Disclosure />
      </div>
    </>
  );
}
