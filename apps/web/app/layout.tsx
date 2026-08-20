import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";
import AnalyticsBeacon from "@/components/AnalyticsBeacon";
import FeedbackControl from "@/components/FeedbackControl";
import SiteHeader from "@/components/SiteHeader";

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_APP_BASE_URL ?? "http://localhost:3000",
  ),
  title: {
    default: "EquityLens — Explainable stock research",
    template: "%s · EquityLens",
  },
  description:
    "Inspect transparent factor rankings, test the method honestly, and track simulated decisions.",
  applicationName: "EquityLens",
  openGraph: { type: "website", siteName: "EquityLens" },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <SiteHeader />
          <AnalyticsBeacon />
          {children}
          <FeedbackControl />
        </Providers>
      </body>
    </html>
  );
}
