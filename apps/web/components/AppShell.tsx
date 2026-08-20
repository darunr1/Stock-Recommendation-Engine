"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  BarChart3,
  BriefcaseBusiness,
  Database,
  FlaskConical,
  LayoutDashboard,
  ListFilter,
  LogOut,
  Settings,
  ShieldCheck,
  Star,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";

const links = [
  ["/dashboard", "Overview", LayoutDashboard],
  ["/screener", "Screener", ListFilter],
  ["/watchlist", "Watchlist", Star],
  ["/backtests", "Backtests", BarChart3],
  ["/paper", "Paper portfolio", BriefcaseBusiness],
  ["/data-health", "Data health", Activity],
  ["/settings", "Settings", Settings],
] as const;

export type CurrentUser = {
  id: string;
  email: string;
  role: string;
  verified: boolean;
  onboarding_completed: boolean;
  activated: boolean;
  is_demo: boolean;
};

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const me = useQuery({
    queryKey: ["me"],
    queryFn: () => api<{ user: CurrentUser }>("/auth/me"),
    retry: false,
  });

  async function logout() {
    await api("/auth/logout", { method: "POST" }).catch(() => undefined);
    queryClient.clear();
    router.push("/login");
  }

  if (me.isLoading)
    return (
      <main className="container loading-state">
        <div>
          <div className="skeleton" style={{ width: 220 }} />
          <p className="muted">Loading the research workspace…</p>
        </div>
      </main>
    );
  if (me.isError || !me.data)
    return (
      <main className="container empty-state">
        <div>
          <span className="eyebrow">Protected research</span>
          <h1 style={{ fontSize: "3rem" }}>Sign in to continue.</h1>
          <p className="lead">
            Public stock snapshots remain available without an account.
          </p>
          <div className="inline-actions" style={{ justifyContent: "center" }}>
            <Link className="button" href="/login">
              Sign in
            </Link>
            <Link className="button secondary" href="/stocks/AAPL">
              View public snapshot
            </Link>
          </div>
        </div>
      </main>
    );
  const user = me.data.user;
  if (!user.verified && pathname !== "/verify-email")
    return (
      <main className="container empty-state">
        <div>
          <span className="eyebrow">Email verification</span>
          <h1 style={{ fontSize: "3rem" }}>
            Verify before opening protected research.
          </h1>
          <p className="lead">
            Check the captured local email in demo development or your inbox in
            production.
          </p>
          <Link className="button" href="/verify-email">
            Use verification link
          </Link>
        </div>
      </main>
    );

  return (
    <div className="workspace">
      <aside className="sidebar">
        <nav aria-label="Research workspace">
          {links.map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
              className={pathname === href ? "active" : ""}
            >
              <Icon size={17} /> {label}
            </Link>
          ))}
          {user.role === "admin" && (
            <>
              <Link
                href="/admin/jobs"
                className={pathname === "/admin/jobs" ? "active" : ""}
              >
                <Database size={17} /> Jobs
              </Link>
              <Link
                href="/admin/product-metrics"
                className={
                  pathname === "/admin/product-metrics" ? "active" : ""
                }
              >
                <ShieldCheck size={17} /> Product metrics
              </Link>
              <Link
                href="/admin/feedback"
                className={pathname === "/admin/feedback" ? "active" : ""}
              >
                <FlaskConical size={17} /> Feedback queue
              </Link>
            </>
          )}
          <button
            className="button ghost"
            onClick={logout}
            style={{ justifyContent: "flex-start", marginTop: ".5rem" }}
          >
            <LogOut size={17} /> Sign out
          </button>
        </nav>
        <div
          style={{
            position: "absolute",
            bottom: "1rem",
            left: "1rem",
            right: "1rem",
          }}
        >
          <span className="status-badge warning">
            {user.is_demo
              ? "Demo account"
              : user.activated
                ? "Activated"
                : "Getting started"}
          </span>
        </div>
      </aside>
      <main className="workspace-main">{children}</main>
    </div>
  );
}
