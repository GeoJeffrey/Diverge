"""
schemas.py

Pydantic response/request models strictly matching the frozen docs/openapi.json contract.
Every field name, type, and nesting matches the OpenAPI spec exactly.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


# ── Health ──

class HealthResponse(BaseModel):
    status: str = Field(..., description="healthy | degraded | unhealthy")
    version: str
    database: str = Field(..., description="connected | disconnected")
    timestamp_utc: str


# ── Error ──

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ── Auth Request / Response ──

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: str


# ── Index Metric Envelope ──

class IndexMetricValue(BaseModel):
    """Standardized index metric envelope per frozen contract."""
    label: str
    score: Optional[float] = None
    available: bool
    coverage_note: Optional[str] = None


# ── Ticker Simple ──

class TickerSimpleItem(BaseModel):
    id: str
    symbol: str
    name: str
    sector: str
    score: Optional[float] = None
    verdict_label: str
    why_sentence: str
    trust_label: str
    window_start_utc: str


class TickerListResponse(BaseModel):
    total: int
    tickers: List[TickerSimpleItem]


class TickerSimpleResponse(TickerSimpleItem):
    """Simple-mode response is a TickerSimpleItem (allOf in OpenAPI)."""
    pass


# ── Ticker Advanced ──

class IndicesBreakdown(BaseModel):
    rn: IndexMetricValue
    cirg: IndexMetricValue
    cli: IndexMetricValue
    cassi: IndexMetricValue
    vdi: IndexMetricValue


class CoordinationMetric(BaseModel):
    label: str
    coordination_score: float
    confidence_flag: str
    available: bool
    coverage_note: Optional[str] = None


class PhylogenyTransitionItem(BaseModel):
    window_start_utc: str
    mutation_type: str
    mutation_detail: Dict[str, Any]
    composite_delta: Optional[float] = None


class TickerAdvancedResponse(BaseModel):
    symbol: str
    name: str
    sector: str
    window_start_utc: str
    window_end_utc: Optional[str] = None
    composite_score: Optional[float] = None
    dominant_index: str
    risk_flags: List[str]
    aggregation_confidence: str
    indices: IndicesBreakdown
    coordination: CoordinationMetric
    phylogeny_context: List[PhylogenyTransitionItem]


# ── Reasoning Trace ──

class ReasoningTraceItem(BaseModel):
    trace_id: int
    post_id: str
    account_id: str
    platform: str
    weight: float
    upvotes: int
    text_preview: str


class ReasoningTraceResponse(BaseModel):
    symbol: str
    window_start_utc: Optional[str] = None
    total_traces: int
    categories: Dict[str, List[ReasoningTraceItem]]
