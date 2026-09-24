"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FrequencyWord, api } from "@/lib/api";

export default function Onboarding() {
  const [words, setWords] = useState<FrequencyWord[]>([]);
  const [known, setKnown] = useState<Set<string>>(new Set());
  const router = useRouter();

  useEffect(() => {
    api<FrequencyWord[]>("/onboarding/sample").then(setWords).catch(console.error);
  }, []);

  function toggle(lemma: string) {
    const next = new Set(known);
    if (next.has(lemma)) next.delete(lemma);
    else next.add(lemma);
    setKnown(next);
  }

  async function submit() {
    await api("/onboarding/seed", {
      method: "POST",
      body: JSON.stringify({ known: [...known], unknown: [] }),
    });
    router.push("/feed");
  }

  return (
    <div className="onboard">
      <h1>Which of these do you already know?</h1>
      <p className="muted">
        A new account starts at 100% unknown. Mark the common lemmas you own so difficulty
        scores mean something on day one.
      </p>
      <ul className="word-grid">
        {words.map((w) => (
          <li key={w.lemma}>
            <button className={known.has(w.lemma) ? "chip on" : "chip"} onClick={() => toggle(w.lemma)}>
              {w.lemma}
            </button>
          </li>
        ))}
      </ul>
      <button onClick={submit}>Seed my vocabulary ({known.size})</button>
    </div>
  );
}
