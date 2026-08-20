import type { MetadataRoute } from "next";

const symbols = [
  "AAPL",
  "MSFT",
  "NVDA",
  "AMZN",
  "GOOGL",
  "META",
  "JPM",
  "V",
  "XOM",
  "WMT",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const base = process.env.NEXT_PUBLIC_APP_BASE_URL ?? "http://localhost:3000";
  return [
    ...["", "/methodology", "/privacy", "/terms", "/changelog"].map((path) => ({
      url: `${base}${path}`,
      changeFrequency: "weekly" as const,
      priority: path === "" ? 1 : 0.6,
    })),
    ...symbols.map((symbol) => ({
      url: `${base}/stocks/${symbol}`,
      changeFrequency: "daily" as const,
      priority: 0.7,
    })),
  ];
}
