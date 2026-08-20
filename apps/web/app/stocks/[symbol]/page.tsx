import type { Metadata } from "next";
import { notFound } from "next/navigation";
import StockExperience from "@/components/StockExperience";
import { serverApi } from "@/lib/api";
import type { Recommendation } from "@/lib/types";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ symbol: string }> };

async function load(symbol: string) {
  return serverApi<Recommendation>(
    `/public/stocks/${encodeURIComponent(symbol.toUpperCase())}`,
  );
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { symbol } = await params;
  const stock = await load(symbol);
  if (!stock)
    return { title: "Stock snapshot unavailable", robots: { index: false } };
  const state = stock.demo ? "Demo research" : stock.band;
  return {
    title: `${stock.symbol} transparent research snapshot`,
    description: `${stock.symbol} ${state}, as of ${stock.as_of_date}. Inspect factor scores and data confidence. Research only.`,
    alternates: { canonical: `/stocks/${stock.symbol}` },
    openGraph: {
      title: `${stock.symbol} · ${stock.band} · EquityLens`,
      description: `Dated ${stock.as_of_date}. Confidence measures completeness and freshness, not certainty.`,
      url: `/stocks/${stock.symbol}`,
      images: [{ url: `/stocks/${stock.symbol}/opengraph-image` }],
    },
    robots: { index: stock.band !== "INSUFFICIENT_DATA", follow: true },
  };
}

export default async function StockPage({ params }: Props) {
  const { symbol } = await params;
  const stock = await load(symbol);
  if (!stock) notFound();
  return <StockExperience initial={stock} />;
}
