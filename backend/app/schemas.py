from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    target_language: str
    target_country: str
    vocab_version: int
    onboarded: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    target_language: str | None = None
    target_country: str | None = None


class TokenSpan(BaseModel):
    text: str
    lemma: str
    is_entity: bool = False
    is_punct: bool = False
    unknown: bool = False


class ArticleListItem(BaseModel):
    id: int
    title: str
    url: str
    source_name: str
    country: str
    language: str
    published_at: datetime
    unknown_pct: float
    unknown_count: int
    content_lemma_count: int


class ArticleDetail(BaseModel):
    id: int
    title: str
    url: str
    source_name: str
    country: str
    language: str
    published_at: datetime
    body: str
    tokens: list[TokenSpan]
    unknown_pct: float


class KnowWordIn(BaseModel):
    lemma: str
    familiarity: int = Field(default=3, ge=1, le=5)


class BulkImportIn(BaseModel):
    lemmas: list[str]
    familiarity: int = Field(default=3, ge=1, le=5)


class OnboardingSeedIn(BaseModel):
    known: list[str]
    unknown: list[str] = []


class FrequencyWord(BaseModel):
    lemma: str
    rank: int


class CacheStats(BaseModel):
    lemma_hits: int
    lemma_misses: int
    score_hits: int
    score_misses: int
    hit_rate: float
    extra: dict[str, Any] = {}
