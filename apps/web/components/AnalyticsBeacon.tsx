"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

type BrowserEvent =
  "landing_viewed" | "signup_started" | "digest_clicked" | "referral_landed";

function anonymousId() {
  const key = "equitylens_anonymous_id";
  const existing = window.localStorage.getItem(key);
  if (existing) return existing;
  const created = crypto.randomUUID();
  window.localStorage.setItem(key, created);
  return created;
}

export function captureBrowserEvent(
  name: BrowserEvent | "share_clicked",
  properties: Record<string, string | number | boolean | null> = {},
) {
  return fetch("/api/v1/events", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-Anonymous-Id": anonymousId(),
    },
    body: JSON.stringify({ name, properties }),
    keepalive: true,
  }).catch(() => undefined);
}

function RouteAnalytics() {
  const pathname = usePathname();
  const search = useSearchParams();

  useEffect(() => {
    let name: BrowserEvent | undefined;
    if (pathname === "/") name = "landing_viewed";
    if (pathname === "/register") name = "signup_started";
    if (pathname === "/unsubscribe") name = "digest_clicked";
    if (pathname.startsWith("/invite/")) name = "referral_landed";
    if (!name) return;
    void captureBrowserEvent(name, {
      path: pathname,
      campaign: search.get("utm_campaign") ?? "direct",
    });
  }, [pathname, search]);

  return null;
}

export default function AnalyticsBeacon() {
  return (
    <Suspense fallback={null}>
      <RouteAnalytics />
    </Suspense>
  );
}
