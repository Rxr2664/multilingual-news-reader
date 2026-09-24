from __future__ import annotations

import re
from dataclasses import dataclass, field

CONTENT_POS = {"NOUN", "VERB", "ADJ", "ADV", "AUX", "ADP", "DET", "PRON", "SCONJ", "CCONJ"}
SKIP_ENT_TYPES = {"PER", "PERSON", "ORG", "GPE", "LOC", "MISC", "NORP", "FAC", "EVENT"}


@dataclass
class Token:
    text: str
    lemma: str
    is_entity: bool = False
    is_punct: bool = False
    pos: str = ""


@dataclass
class ProcessedArticle:
    tokens: list[Token] = field(default_factory=list)
    lemmas: list[str] = field(default_factory=list)
    content_lemma_count: int = 0


_punct_re = re.compile(r"^[\W_]+$", re.UNICODE)


def fallback_tokenize(text: str) -> ProcessedArticle:
    """Used in tests and when spaCy models are missing."""
    tokens: list[Token] = []
    lemmas: list[str] = []
    for raw in re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE):
        is_punct = bool(_punct_re.match(raw))
        lemma = raw.lower() if not is_punct else raw
        token = Token(text=raw, lemma=lemma, is_punct=is_punct, pos="PUNCT" if is_punct else "NOUN")
        tokens.append(token)
        if not is_punct and not raw[0].isupper():
            lemmas.append(lemma)
    content = [t.lemma for t in tokens if not t.is_punct and not t.is_entity]
    return ProcessedArticle(tokens=tokens, lemmas=sorted(set(lemmas)), content_lemma_count=len(set(content)))


def from_spacy_doc(doc) -> ProcessedArticle:
    tokens: list[Token] = []
    content_lemmas: set[str] = set()
    for t in doc:
        is_punct = t.is_punct or t.is_space
        is_entity = bool(t.ent_type_) and t.ent_type_ in SKIP_ENT_TYPES
        lemma = (t.lemma_ or t.text).lower()
        tokens.append(
            Token(
                text=t.text_with_ws if False else t.text,
                lemma=lemma,
                is_entity=is_entity,
                is_punct=is_punct,
                pos=t.pos_,
            )
        )
        if not is_punct and not is_entity and t.pos_ != "NUM" and lemma.isalpha():
            content_lemmas.add(lemma)
    return ProcessedArticle(
        tokens=tokens,
        lemmas=sorted(content_lemmas),
        content_lemma_count=len(content_lemmas),
    )


def token_to_dict(t: Token) -> dict:
    return {
        "text": t.text,
        "lemma": t.lemma,
        "is_entity": t.is_entity,
        "is_punct": t.is_punct,
        "pos": t.pos,
    }
