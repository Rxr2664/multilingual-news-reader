"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { ArticleListItem, api } from "@/lib/api";
import { difficultyBand } from "@/components/TokenReader";

export default function FeedPage() {
  const [items, setItems] = useState<ArticleListItem[]>([]);
  const [sort, setSort] = useState<"difficulty" | "newest">("difficulty");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api<ArticleListItem[]>(`/articles?sort=${sort}`)
      .then(setItems)
      .catch((e) => setErr(String(e)));
  }, [sort]);

  return (
    <Shell>
      <div className="feed-head">
        <div>
          <h1>Today&apos;s feed</h1>
          <p className="muted">Sorted by how much of each article is still unknown to you.</p>
        </div>
        <div className="sort">
          <button className={sort === "difficulty" ? "chip on" : "chip"} onClick={() => setSort("difficulty")}>
            By difficulty
          </button>
          <button className={sort === "newest" ? "chip on" : "chip"} onClick={() => setSort("newest")}>
            Newest
          </button>
        </div>
      </div>
      {err && <p className="error">{err}</p>}
      {!items.length && !err && (
        <p className="muted">No articles yet. The worker polls RSS every 15 minutes.</p>
      )}
      <ul className="feed">
        {items.map((a) => (
          <li key={a.id}>
            <Link href={`/article/${a.id}`}>
              <span className={`pct ${difficultyBand(a.unknown_pct)}`}>{a.unknown_pct.toFixed(0)}% unknown</span>
              <span className="meta">
                {a.source_name} · {new Date(a.published_at).toLocaleString()}
              </span>
              <strong>{a.title}</strong>
            </Link>
          </li>
        ))}
      </ul>
    </Shell>
  );
}
