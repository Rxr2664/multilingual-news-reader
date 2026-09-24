# Design notes — Multilingual News Reader

This is the working design for the product. Edit it as the implementation drifts.

## Product

You are learning a language by reading real news. The wall is unknown vocabulary. The app scores every article against *your* lemma vocabulary, highlights the words you do not know, and lets a single “I know this” update every score in the corpus.

An article is a set of lemmas. Your vocabulary is a set of lemmas. Unknown = article − vocabulary. Surface forms are collapsed with spaCy so *parlaient* / *parlerai* / *parlons* are all *parler*.

## Components

| Piece | Role |
| --- | --- |
| Worker | Poll 20 RSS feeds / 4 countries every 15 minutes. Fetch body, lemmatize, store, fill lemma cache + reverse index. |
| API | FastAPI. Feed with per-user difficulty, article tokens, vocab updates, Google OAuth + JWT, demo login. |
| Web | Next.js. One span per token, optimistic known-word updates, onboarding frequency sample. |
| Postgres | sources, articles, article_lemmas, users, known_words |
| Redis | lemma blobs, score keys, lemma→article sets |

One `docker-compose.yml`. Grafana scrapes `/metrics`.

## Invalidation rule

- One lemma: reverse index, precise unlink, rest of the cache stays warm.
- Bulk (≥ `BULK_INVALIDATION_THRESHOLD`, default 50): increment `vocab_version`. Stampede of deletes is worse than letting old keys rot.

## Hard parts we accepted

- Lemmatization is ambiguous (*est*, *porte*). spaCy uses sentence context; we do not post-edit.
- Named entities are not vocabulary. They are excluded from difficulty.
- Familiarity is an integer 1–5 on `known_words` but the scorer still treats presence as known. Spaced repetition can consume that column later.
- Cold start: onboarding marks a frequency list.
- Dedup: SHA-256 of whitespace-normalized body. Near-duplicates are out of scope.

## Interview numbers to re-measure

Time the feed query with `EXPLAIN ANALYZE` before and after `ix_articles_source_published`. Time a page of 500 scores with a cold vs warm score cache. Point Grafana at hit rate after a bulk import vs after a single learn.
