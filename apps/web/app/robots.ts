import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const base = process.env.NEXT_PUBLIC_APP_BASE_URL ?? "http://localhost:3000";
  return {
    rules: [
      {
        userAgent: "*",
        allow: [
          "/",
          "/methodology",
          "/stocks/",
          "/privacy",
          "/terms",
          "/changelog",
        ],
        disallow: [
          "/dashboard",
          "/screener",
          "/watchlist",
          "/backtests",
          "/paper",
          "/settings",
          "/data-health",
          "/admin/",
        ],
      },
    ],
    sitemap: `${base}/sitemap.xml`,
  };
}
