"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Shell from "@/components/Shell";
import TokenReader from "@/components/TokenReader";
import { ArticleDetail, api } from "@/lib/api";

export default function ArticlePage() {
  const params = useParams<{ id: string }>();
  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  async function load() {
    const data = await api<ArticleDetail>(`/articles/${params.id}`);
    setArticle(data);
  }

  useEffect(() => {
    load().catch(console.error);
  }, [params.id]);

  async function know(lemma: string) {
    if (!article) return;
    setArticle({
      ...article,
      tokens: article.tokens.map((t) => (t.lemma === lemma ? { ...t, unknown: false } : t)),
    });
    setSelected(null);
    await api("/vocab/know", { method: "POST", body: JSON.stringify({ lemma }) });
  }

  async function unknown(lemma: string) {
    if (!article) return;
    setArticle({
      ...article,
      tokens: article.tokens.map((t) =>
        t.lemma === lemma && !t.is_entity && !t.is_punct ? { ...t, unknown: true } : t
      ),
    });
    setSelected(null);
    await api("/vocab/unknown", { method: "POST", body: JSON.stringify({ lemma }) });
  }

  if (!article) return <Shell><p className="muted">Loading article…</p></Shell>;

  return (
    <Shell>
      <article className="story">
        <p className="meta">
          {article.source_name} · {article.unknown_pct.toFixed(0)}% unknown ·{" "}
          <a href={article.url} target="_blank" rel="noreferrer">
            original
          </a>
        </p>
        <h1>{article.title}</h1>
        <TokenReader
          tokens={article.tokens}
          selected={selected}
          onSelect={setSelected}
          onKnow={know}
          onUnknown={unknown}
        />
      </article>
    </Shell>
  );
}
