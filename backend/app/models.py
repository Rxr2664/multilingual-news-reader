from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    feed_url: Mapped[str] = mapped_column(String(500), unique=True)
    country: Mapped[str] = mapped_column(String(8), index=True)
    language: Mapped[str] = mapped_column(String(8), index=True)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    articles: Mapped[list["Article"]] = relationship(back_populates="source")


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_source_published", "source_id", "published_at"),
        UniqueConstraint("content_hash", name="uq_articles_content_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1000), unique=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    language: Mapped[str] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[Source] = relationship(back_populates="articles")
    lemma_row: Mapped["ArticleLemma"] = relationship(back_populates="article", uselist=False)


class ArticleLemma(Base):
    __tablename__ = "article_lemmas"

    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), primary_key=True)
    tokens: Mapped[list] = mapped_column(JSONB)
    lemmas: Mapped[list] = mapped_column(JSONB)
    content_lemma_count: Mapped[int] = mapped_column(Integer, default=0)

    article: Mapped[Article] = relationship(back_populates="lemma_row")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_sub: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    target_language: Mapped[str] = mapped_column(String(8), default="fr")
    target_country: Mapped[str] = mapped_column(String(8), default="FR")
    vocab_version: Mapped[int] = mapped_column(Integer, default=1)
    onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    known_words: Mapped[list["KnownWord"]] = relationship(back_populates="user")


class KnownWord(Base):
    __tablename__ = "known_words"
    __table_args__ = (
        UniqueConstraint("user_id", "lemma", name="uq_known_words_user_lemma"),
        Index("ix_known_words_user_lemma", "user_id", "lemma"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lemma: Mapped[str] = mapped_column(String(200))
    familiarity: Mapped[int] = mapped_column(Integer, default=3)
    learned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="known_words")
