"""
models.py

SQLAlchemy declarative ORM models matching the Diverge schema.
Includes all existing analytical tables plus the production User table for JWT authentication.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    Boolean,
    ForeignKey,
    Index,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="standard", nullable=False)  # 'standard', 'pro', 'admin'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(String(50), default=utc_now_iso, nullable=False)


class RawPost(Base):
    __tablename__ = "raw_posts"

    post_id = Column(String(128), primary_key=True)
    account_id = Column(String(128), nullable=False)
    timestamp_utc = Column(String(50), nullable=False)
    community = Column(String(128), nullable=True)
    ticker = Column(String(32), nullable=True)
    raw_text = Column(Text, nullable=True)
    upvotes = Column(Integer, default=0)
    platform = Column(String(64), nullable=False)
    scraped_at = Column(String(50), nullable=False, default=utc_now_iso)

    # Relationships
    timing = relationship("PostTiming", back_populates="post", uselist=False, cascade="all, delete-orphan")
    features = relationship("TextFeature", back_populates="post", uselist=False, cascade="all, delete-orphan")
    reasoning_traces = relationship("ReasoningTrace", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ticker_time", "ticker", "timestamp_utc"),
        Index("idx_account_ticker", "account_id", "ticker"),
    )


class PostTiming(Base):
    __tablename__ = "post_timing"

    post_id = Column(String(128), ForeignKey("raw_posts.post_id"), primary_key=True)
    ticker = Column(String(32), nullable=False)
    timestamp_utc = Column(String(50), nullable=False)
    delta_seconds = Column(Float, nullable=True)
    is_first_mention = Column(Integer, default=0)
    computed_at = Column(String(50), nullable=False, default=utc_now_iso)

    post = relationship("RawPost", back_populates="timing")

    __table_args__ = (
        Index("idx_timing_ticker_time", "ticker", "timestamp_utc"),
    )


class TickerTimeBin(Base):
    __tablename__ = "ticker_time_bins"

    ticker = Column(String(32), nullable=False)
    bin_start_utc = Column(String(50), nullable=False)
    post_count = Column(Integer, default=0)

    __table_args__ = (
        PrimaryKeyConstraint("ticker", "bin_start_utc"),
    )


class TextFeature(Base):
    __tablename__ = "text_features"

    post_id = Column(String(128), ForeignKey("raw_posts.post_id"), primary_key=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(32), nullable=True)
    capitulation_flag = Column(Integer, nullable=True)
    capitulation_confidence = Column(Float, nullable=True)
    is_sarcastic = Column(Integer, nullable=True)
    irony_adjusted_sentiment = Column(Float, nullable=True)
    conviction_hedge_ratio = Column(Float, nullable=True)
    language = Column(String(32), nullable=True)
    computed_at = Column(String(50), nullable=False, default=utc_now_iso)

    post = relationship("RawPost", back_populates="features")


class PeriodicityStat(Base):
    __tablename__ = "periodicity_stats"

    ticker = Column(String(32), nullable=False)
    window_start_utc = Column(String(50), nullable=False)
    window_end_utc = Column(String(50), nullable=False)
    ks_statistic = Column(Float, nullable=True)
    acf_peak_lag_minutes = Column(Float, nullable=True)
    acf_peak_strength = Column(Float, nullable=True)
    dominant_frequency_minutes = Column(Float, nullable=True)
    onset_dispersion_index = Column(Float, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint("ticker", "window_start_utc"),
    )


class IndexValue(Base):
    __tablename__ = "index_values"

    ticker = Column(String(32), nullable=False)
    window_start_utc = Column(String(50), nullable=False)
    window_end_utc = Column(String(50), nullable=True)
    rn = Column(Float, nullable=True)
    rn_confidence = Column(Float, nullable=True)
    cirg = Column(Float, nullable=True)
    cli = Column(Float, nullable=True)
    cassi = Column(Float, nullable=True)
    vdi = Column(Float, nullable=True)
    computed_at = Column(String(50), nullable=False, default=utc_now_iso)

    __table_args__ = (
        PrimaryKeyConstraint("ticker", "window_start_utc"),
    )


class ConsumerSentiment(Base):
    __tablename__ = "consumer_sentiment"

    id = Column(String(64), primary_key=True)
    ticker = Column(String(32), nullable=False)
    timestamp_utc = Column(String(50), nullable=False)
    review_sentiment_score = Column(Float, nullable=False)
    source = Column(String(128), nullable=False)
    raw_text = Column(Text, nullable=True)
    created_at = Column(String(50), nullable=False, default=utc_now_iso)

    __table_args__ = (
        Index("idx_consumer_ticker_time", "ticker", "timestamp_utc"),
    )


class CoordinationScore(Base):
    __tablename__ = "coordination_scores"

    ticker = Column(String(32), nullable=False)
    window_start_utc = Column(String(50), nullable=False)
    window_end_utc = Column(String(50), nullable=True)
    ks_component = Column(Float, nullable=True)
    acf_component = Column(Float, nullable=True)
    onset_component = Column(Float, nullable=True)
    duplicate_ratio = Column(Float, nullable=True)
    sentiment_variance = Column(Float, nullable=True)
    coordination_score = Column(Float, nullable=True)
    confidence_flag = Column(String(32), nullable=True)
    computed_at = Column(String(50), nullable=False, default=utc_now_iso)

    __table_args__ = (
        PrimaryKeyConstraint("ticker", "window_start_utc"),
        Index("idx_coord_ticker_time", "ticker", "window_start_utc"),
    )


class TickerWindowMetric(Base):
    __tablename__ = "ticker_window_metrics"

    ticker = Column(String(32), nullable=False)
    window_start_utc = Column(String(50), nullable=False)
    window_end_utc = Column(String(50), nullable=True)
    rn = Column(Float, nullable=True)
    rn_confidence = Column(Float, nullable=True)
    cirg = Column(Float, nullable=True)
    cli = Column(Float, nullable=True)
    cassi = Column(Float, nullable=True)
    vdi = Column(Float, nullable=True)
    coordination_score = Column(Float, nullable=True)
    confidence_flag = Column(String(32), nullable=True)
    composite_score = Column(Float, nullable=True)
    dominant_index = Column(String(32), nullable=True)
    risk_flags = Column(Text, nullable=True)
    aggregation_confidence = Column(String(32), nullable=True)
    computed_at = Column(String(50), nullable=False, default=utc_now_iso)

    __table_args__ = (
        PrimaryKeyConstraint("ticker", "window_start_utc"),
        Index("idx_twm_ticker_time", "ticker", "window_start_utc"),
    )


class ReasoningTrace(Base):
    __tablename__ = "reasoning_trace"

    trace_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(32), nullable=False)
    window_start_utc = Column(String(50), nullable=False)
    post_id = Column(String(128), ForeignKey("raw_posts.post_id"), nullable=False)
    contributed_to = Column(String(64), nullable=False)
    weight = Column(Float, nullable=False)
    created_at = Column(String(50), nullable=False, default=utc_now_iso)

    post = relationship("RawPost", back_populates="reasoning_traces")

    __table_args__ = (
        Index("idx_trace_ticker_time", "ticker", "window_start_utc"),
    )


class DuplicatePair(Base):
    __tablename__ = "duplicate_pairs"

    ticker = Column(String(32), nullable=False)
    window_start_utc = Column(String(50), nullable=False)
    post_id_a = Column(String(128), nullable=False)
    post_id_b = Column(String(128), nullable=False)
    similarity = Column(Float, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("ticker", "window_start_utc", "post_id_a", "post_id_b"),
    )


class NarrativePhylogeny(Base):
    __tablename__ = "narrative_phylogeny"

    ticker = Column(String(32), nullable=False)
    window_start_utc = Column(String(50), nullable=False)
    window_end_utc = Column(String(50), nullable=True)
    parent_window_start_utc = Column(String(50), nullable=True)
    mutation_type = Column(String(64), nullable=False)
    mutation_detail = Column(Text, nullable=True)
    composite_delta = Column(Float, nullable=True)
    computed_at = Column(String(50), nullable=False, default=utc_now_iso)

    __table_args__ = (
        PrimaryKeyConstraint("ticker", "window_start_utc"),
        Index("idx_phylogeny_ticker_time", "ticker", "window_start_utc"),
    )
