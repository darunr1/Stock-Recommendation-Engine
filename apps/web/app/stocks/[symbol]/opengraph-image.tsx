import { ImageResponse } from "next/og";
import { serverApi } from "@/lib/api";
import type { Recommendation } from "@/lib/types";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const dynamic = "force-dynamic";

export default async function Image({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = await params;
  const stock = await serverApi<Recommendation>(
    `/public/stocks/${symbol.toUpperCase()}`,
  );
  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "72px",
        color: "#edf6ef",
        background: "#10291f",
        fontFamily: "sans-serif",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ fontSize: 42, fontWeight: 700 }}>EquityLens</div>
        <div style={{ color: "#c8f06f", fontSize: 24 }}>
          Research only · {stock?.demo ? "demo data" : "dated snapshot"}
        </div>
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div
            style={{ fontSize: 126, fontWeight: 800, letterSpacing: "-8px" }}
          >
            {stock?.symbol ?? symbol.toUpperCase()}
          </div>
          <div style={{ fontSize: 34, color: "#a7bcb2" }}>
            {stock?.company_name ?? "Snapshot unavailable"}
          </div>
          <div style={{ marginTop: 28, fontSize: 29 }}>
            {stock?.band ?? "Data unavailable"} · As of{" "}
            {stock?.as_of_date ?? "—"}
          </div>
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <div
            style={{
              fontSize: 138,
              fontWeight: 800,
              color: "#c8f06f",
              lineHeight: 1,
            }}
          >
            {stock?.score?.toFixed(0) ?? "—"}
          </div>
          <div style={{ fontSize: 24, color: "#a7bcb2" }}>Composite / 100</div>
        </div>
      </div>
    </div>,
    size,
  );
}
