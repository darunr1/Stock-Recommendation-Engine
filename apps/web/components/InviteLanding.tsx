"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

function anonymousId() {
  const existing = localStorage.getItem("equitylens-anon");
  if (existing) return existing;
  const created = crypto.randomUUID();
  localStorage.setItem("equitylens-anon", created);
  return created;
}

export default function InviteLanding({ code }: { code: string }) {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    api("/attribution/landing", {
      method: "POST",
      body: JSON.stringify({
        anonymous_id: anonymousId(),
        referral_code: code,
        landing_path: `/invite/${code}`,
      }),
    }).finally(() => setReady(true));
  }, [code]);
  return (
    <main className="article">
      <span className="eyebrow">Research invitation</span>
      <h1>Inspect the method before you join.</h1>
      <p className="lead">
        The invitation has no financial reward and reveals no inviter identity.
        It only attributes an aggregate product referral.
      </p>
      <div className="inline-actions">
        <Link className="button" href="/stocks/AAPL">
          Open a public snapshot
        </Link>
        <Link className="button secondary" href="/register">
          {ready ? "Create my account" : "Recording attribution…"}
        </Link>
      </div>
    </main>
  );
}
