def unknown_pct(article_lemmas: list[str] | set[str], known: set[str]) -> tuple[float, int]:
    lemmas = {l.lower() for l in article_lemmas if l}
    if not lemmas:
        return 0.0, 0
    unknown = lemmas - known
    pct = round(100.0 * len(unknown) / len(lemmas), 1)
    return pct, len(unknown)
