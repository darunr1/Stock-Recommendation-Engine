"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { ScoreBadge } from "@/components/ResearchUI";
import { api } from "@/lib/api";
import type { Recommendation } from "@/lib/types";
import { PageHead, QueryState } from "./Shared";

type WatchItem = Recommendation & { note: string; added_at: string };
export default function Watchlist() {
  const queryClient = useQueryClient();
  const [symbol, setSymbol] = useState("AAPL");
  const [message, setMessage] = useState("");
  const query = useQuery({
    queryKey: ["watchlist"],
    queryFn: () => api<{ items: WatchItem[] }>("/watchlist"),
  });
  const add = useMutation({
    mutationFn: () =>
      api("/watchlist/items", {
        method: "POST",
        body: JSON.stringify({ symbol, note: "" }),
      }),
    onSuccess: () => {
      setMessage(`${symbol.toUpperCase()} added.`);
      void queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
    onError: (error) => setMessage(error.message),
  });
  async function submit(event: FormEvent) {
    event.preventDefault();
    add.mutate();
  }
  async function remove(item: string) {
    await api(`/watchlist/items/${item}`, { method: "DELETE" });
    void queryClient.invalidateQueries({ queryKey: ["watchlist"] });
  }
  return (
    <>
      <PageHead
        eyebrow="Saved research"
        title="Watchlist"
        copy="Track score state and keep a short research note—never a live holding."
        action={
          <form className="inline-actions" onSubmit={submit}>
            <label>
              <span className="sr-only">Symbol</span>
              <input
                value={symbol}
                onChange={(event) =>
                  setSymbol(event.target.value.toUpperCase())
                }
                maxLength={12}
              />
            </label>
            <button className="button" disabled={add.isPending}>
              Add symbol
            </button>
          </form>
        }
      />
      {message && (
        <p className="form-message" role="status">
          {message}
        </p>
      )}
      <QueryState
        loading={query.isLoading}
        error={query.error}
        empty={query.data?.items.length === 0}
        onRetry={() => void query.refetch()}
      />
      {query.data?.items.length ? (
        <section className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Research state</th>
                  <th>Confidence</th>
                  <th>Strongest contributor</th>
                  <th>Added</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {query.data.items.map((item) => (
                  <tr key={item.symbol}>
                    <td>
                      <Link href={`/stocks/${item.symbol}`}>
                        <strong>{item.symbol}</strong>
                        <span
                          className="muted"
                          style={{ display: "block", fontSize: ".72rem" }}
                        >
                          {item.company_name}
                        </span>
                      </Link>
                    </td>
                    <td>
                      <ScoreBadge score={item.score} band={item.band} />
                    </td>
                    <td title={item.confidence_help}>
                      {item.confidence.toFixed(0)}%
                    </td>
                    <td>{item.contributors[0]?.label ?? "—"}</td>
                    <td>{item.added_at.slice(0, 10)}</td>
                    <td>
                      <button
                        className="button ghost"
                        onClick={() => remove(item.symbol)}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </>
  );
}
