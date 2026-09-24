"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Shell from "@/components/Shell";
import TokenReader from "@/components/TokenReader";
import { ArticleDetail, TokenSpan, api } from "@/lib/api";

function setLemmaUnknown(tokens: TokenSpan[], lemma: string, unknown: boolean): TokenSpan[] {
  return tokens.map((t) =>
    t.lemma === lemma && !t.is_entity && !t.is_punct ? { ...t, unknown } : t
  );
}

export default function ArticlePage() {
  const params = useParams<{ id: string }>();
  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const data = await api<ArticleDetail>(`/articles/${params.id}`);
    setArticle(data);
  }

  useEffect(() => {
    load().catch(console.error);
  }, [params.id]);

  async function mark(lemma: string, unknown: boolean) {
    if (!article) return;
    const previous = article.tokens;
    setArticle((cur) => cur && { ...cur, tokens: setLemmaUnknown(cur.tokens, lemma, unknown) });
    setSelected(null);
    setError(null);
    try {
      await api(unknown ? "/vocab/unknown" : "/vocab/know", {
        method: "POST",
        body: JSON.stringify({ lemma }),
      });
    } catch {
      // Put back only this lemma's tokens, so other words marked meanwhile keep their state.
      setArticle(
        (cur) =>
          cur && {
            ...cur,
            tokens: cur.tokens.map((t, i) =>
              t.lemma === lemma ? { ...t, unknown: previous[i].unknown } : t
            ),
          }
      );
      setError(`Couldn't save "${lemma}". Please try again.`);
    }
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
        {error && <p className="error">{error}</p>}
        <TokenReader
          tokens={article.tokens}
          selected={selected}
          onSelect={setSelected}
          onKnow={(lemma) => mark(lemma, false)}
          onUnknown={(lemma) => mark(lemma, true)}
        />
      </article>
    </Shell>
  );
}
