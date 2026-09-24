# Multilingual News Reader (Lemma)

Full-stack reader for authentic news in French, Spanish, German, and Italian. Difficulty is the share of lemmas you do not know yet. The worker lemmatizes once; the API scores per user against a persistent vocabulary.

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

- App: http://localhost:3000
- API: http://localhost:8000
- Grafana: http://localhost:3001 (admin / admin)
- Prometheus: http://localhost:9090

Demo login works without Google. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` for OAuth.

Without Docker, start Postgres and Redis, then:

```bash
cd backend && pip install -r requirements.txt && python -m spacy download fr_core_news_sm
uvicorn app.main:app --reload
python -m worker.main
cd ../frontend && npm install && npm run dev
```

## Tests

GitHub Actions runs pytest against real Postgres/Redis and Jest for the token reader.

```bash
cd backend && pytest
cd frontend && npm test
```

## Caching

1. **Article lemmas** — cache-aside, long TTL, identical for every user.
2. **Per-user scores** — `score:{user_id}:{vocab_version}:{article_id}`.
3. **Single-word learn** — reverse index `lemma_index:{lemma}` → unlink those score keys.
4. **Bulk import** (≥50 lemmas) — bump `users.vocab_version`. Old keys expire on TTL.

## Indexes

- `known_words (user_id, lemma)`
- `articles (source_id, published_at DESC)`
