from app.services.difficulty import unknown_pct
from app.services.nlp import fallback_tokenize


def test_unknown_pct_empty():
    assert unknown_pct([], set()) == (0.0, 0)


def test_unknown_pct_all_unknown():
    pct, n = unknown_pct(["parler", "malgré"], set())
    assert pct == 100.0
    assert n == 2


def test_unknown_pct_after_learn():
    pct, n = unknown_pct(["parler", "malgré"], {"parler"})
    assert pct == 50.0
    assert n == 1


def test_fallback_tokenize_lemmas():
    processed = fallback_tokenize("Les chats parlaient.")
    assert "chats" in processed.lemmas or "parlaient" in processed.lemmas
    assert processed.content_lemma_count >= 1
