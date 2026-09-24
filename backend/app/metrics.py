from prometheus_client import Counter, Histogram

lemma_cache_hits = Counter("lemma_cache_hits_total", "Article lemma cache hits")
lemma_cache_misses = Counter("lemma_cache_misses_total", "Article lemma cache misses")
score_cache_hits = Counter("score_cache_hits_total", "Difficulty score cache hits")
score_cache_misses = Counter("score_cache_misses_total", "Difficulty score cache misses")
score_invalidations = Counter(
    "score_invalidations_total", "Score keys deleted via reverse index", ["strategy"]
)
feed_query_seconds = Histogram("feed_query_seconds", "Article feed SQL time")
nlp_seconds = Histogram("nlp_article_seconds", "spaCy lemmatization time")
worker_articles_ingested = Counter(
    "worker_articles_ingested_total", "Articles ingested by worker", ["language"]
)
