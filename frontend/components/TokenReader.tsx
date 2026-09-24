"use client";

import { TokenSpan } from "@/lib/api";

type Props = {
  tokens: TokenSpan[];
  onKnow: (lemma: string) => void;
  onUnknown: (lemma: string) => void;
  selected: string | null;
  onSelect: (lemma: string | null) => void;
};

export function difficultyBand(pct: number): string {
  if (pct < 8) return "comfort";
  if (pct < 20) return "stretch";
  return "hard";
}

export default function TokenReader({ tokens, onKnow, onUnknown, selected, onSelect }: Props) {
  return (
    <p className="reader">
      {tokens.map((t, i) => {
        if (t.is_punct) {
          return <span key={i}>{t.text}</span>;
        }
        const cls = [
          "token",
          t.unknown ? "unknown" : "",
          t.is_entity ? "entity" : "",
          selected === t.lemma ? "selected" : "",
        ]
          .filter(Boolean)
          .join(" ");
        return (
          <span
            key={i}
            className={cls}
            onClick={() => !t.is_entity && onSelect(t.lemma)}
            data-lemma={t.lemma}
          >
            {t.text}
          </span>
        );
      })}
      {selected && (
        <span className="popover" role="dialog">
          <strong>{selected}</strong>
          <button type="button" onClick={() => onKnow(selected)}>
            I know this
          </button>
          <button type="button" className="ghost" onClick={() => onUnknown(selected)}>
            Still learning
          </button>
          <button type="button" className="ghost" onClick={() => onSelect(null)}>
            Close
          </button>
        </span>
      )}
    </p>
  );
}
