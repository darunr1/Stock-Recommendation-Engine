"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import Disclosure from "@/components/Disclosure";
import { api } from "@/lib/api";

export default function AccountDeletionPanel() {
  const router = useRouter();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function cancelDeletion() {
    setBusy(true);
    setMessage("");
    try {
      await api("/account/delete-cancel", { method: "POST" });
      router.push("/dashboard");
      router.refresh();
    } catch (reason) {
      setMessage(
        reason instanceof Error
          ? reason.message
          : "The deletion request could not be cancelled.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="narrow-page">
      <section className="auth-card form-grid">
        <span className="eyebrow">Reversible grace period</span>
        <h1>Account deletion is scheduled</h1>
        <p className="muted">
          Lifecycle email and existing refresh sessions are disabled. Cancel
          during the grace period to retain your research history.
        </p>
        <button className="button" disabled={busy} onClick={cancelDeletion}>
          {busy ? "Cancellingâ€¦" : "Cancel deletion and keep my account"}
        </button>
        <Link className="button ghost" href="/privacy">
          Review the privacy policy
        </Link>
        {message && <p className="form-message error">{message}</p>}
        <Disclosure compact />
      </section>
    </main>
  );
}
