"""
tickers.py

Ticker data endpoints matching the frozen openapi.json contract:
  GET /tickers
  GET /ticker/{symbol}
  GET /ticker/{symbol}/simple
  GET /ticker/{symbol}/reasoning
"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, get_optional_current_user
from ..schemas import (
    TickerListResponse,
    TickerSimpleItem,
    TickerSimpleResponse,
    TickerAdvancedResponse,
    IndicesBreakdown,
    IndexMetricValue,
    CoordinationMetric,
    PhylogenyTransitionItem,
    ReasoningTraceResponse,
    ReasoningTraceItem,
    ErrorResponse,
)
from ..ticker_metadata import get_ticker_name, get_ticker_sector, TICKER_INFO
from ...db.models import User

router = APIRouter(tags=["Tickers & Detail"])


# ── Approved Index Labels ──
INDEX_LABELS = {
    "rn": "Contagion Core",
    "cirg": "Reality Check",
    "cli": "Capitulation Signal",
    "cassi": "Cross-Market Spillover",
    "vdi": "Language Divergence",
}

TRUST_LABEL_MAP = {
    "high_trust": "High confidence",
    "moderate": "Moderate confidence - treat with caution",
    "low_trust": "Low confidence - possible manipulation detected",
    "insufficient_data": "Not enough data",
}


def _build_index_metric(label: str, score, index_key: str = "") -> IndexMetricValue:
    """Build an IndexMetricValue envelope from a raw score."""
    if score is None:
        coverage_notes = {
            "rn": "Needs 3+ distinct days with first-mention posts for this ticker",
            "cirg": "Needs investor sentiment and consumer review data for comparison",
            "cli": "Needs posts with capitulation language signals",
            "cassi": "Needs 7+ days of overlapping multi-ticker sentiment data",
            "vdi": "Needs posts in 2+ language groups for divergence comparison",
        }
        return IndexMetricValue(
            label=label,
            score=None,
            available=False,
            coverage_note=coverage_notes.get(index_key, "Insufficient data to compute this index"),
        )
    return IndexMetricValue(
        label=label,
        score=round(float(score), 4),
        available=True,
        coverage_note=None,
    )


def _build_verdict_label(score) -> str:
    if score is None:
        return "insufficient_data"
    s = float(score)
    if s < 35.0:
        return "fading"
    elif s < 65.0:
        return "mixed"
    return "building"


def _build_why_sentence(dominant_index: str, row: Dict[str, Any], risk_flags: List[str]) -> str:
    """Generate plain-language why sentence."""
    if dominant_index == "insufficient_data" or dominant_index is None:
        return "Not enough data yet for a reliable reading."

    rn_val = row.get("rn")
    cirg_val = row.get("cirg")
    cli_val = row.get("cli")
    cassi_val = row.get("cassi")
    vdi_val = row.get("vdi")

    if dominant_index == "rn":
        rn_str = f" (Rn {rn_val:.2f})" if rn_val is not None else ""
        base = f"Narrative momentum driven by virality rate{rn_str}."
    elif dominant_index == "cassi":
        cassi_str = f" (CASSI {cassi_val:.2f})" if cassi_val is not None else ""
        base = f"Cross-asset sentiment spillover{cassi_str} driving retail interest."
    elif dominant_index == "vdi":
        vdi_str = f" (VDI {vdi_val:.2f})" if vdi_val is not None else ""
        base = f"Language divergence between English and regional commentary{vdi_str}."
    elif dominant_index == "cirg":
        cirg_str = f" (CIRG {cirg_val:.2f})" if cirg_val is not None else ""
        base = f"Reality gap between consumer sentiment and investor narrative{cirg_str}."
    elif dominant_index == "cli":
        cli_str = f" (CLI {cli_val:.2f})" if cli_val is not None else ""
        base = f"Capitulation signals detected across social channels{cli_str}."
    else:
        base = f"Narrative score driven by {dominant_index} index."

    flag_clauses = []
    if "hype_outrunning_reality" in risk_flags:
        flag_clauses.append("hype currently outrunning consumer reality")
    if "consumer_reality_underpriced" in risk_flags:
        flag_clauses.append("consumer sentiment indicates market may be underpricing reality")
    if "capitulation_signal" in risk_flags:
        flag_clauses.append("capitulation signals detected across social channels")

    if flag_clauses:
        return f"{base} - {'; '.join(flag_clauses)}."
    return base


def _get_latest_window_row(db: Session, symbol: str, window: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch a ticker_window_metrics row (latest or specific window)."""
    if window:
        result = db.execute(
            text("SELECT * FROM ticker_window_metrics WHERE ticker = :t AND window_start_utc = :w"),
            {"t": symbol.upper(), "w": window},
        ).mappings().first()
    else:
        result = db.execute(
            text("""
                SELECT * FROM ticker_window_metrics
                WHERE ticker = :t
                ORDER BY (composite_score IS NOT NULL) DESC, window_start_utc DESC
                LIMIT 1
            """),
            {"t": symbol.upper()},
        ).mappings().first()
    return dict(result) if result else None


def _build_simple_item(row: Dict[str, Any], symbol: str) -> TickerSimpleItem:
    """Build a TickerSimpleItem from a ticker_window_metrics row."""
    score = row.get("composite_score")
    dom_index = row.get("dominant_index", "insufficient_data")
    conf_flag = row.get("confidence_flag", "insufficient_data") or "insufficient_data"

    try:
        rf_raw = row.get("risk_flags", "[]")
        risk_flags = json.loads(rf_raw) if isinstance(rf_raw, str) else (rf_raw or [])
    except Exception:
        risk_flags = []

    return TickerSimpleItem(
        id=symbol.upper(),
        symbol=symbol.upper(),
        name=get_ticker_name(symbol),
        sector=get_ticker_sector(symbol),
        score=round(float(score), 1) if score is not None else None,
        verdict_label=_build_verdict_label(score),
        why_sentence=_build_why_sentence(dom_index, row, risk_flags),
        trust_label=TRUST_LABEL_MAP.get(conf_flag, "Moderate confidence - treat with caution"),
        window_start_utc=row.get("window_start_utc", ""),
    )


# ── GET /tickers ──

@router.get("/tickers", response_model=TickerListResponse)
def get_tickers(db: Session = Depends(get_db)):
    """List tracked market tickers with latest sentiment verdict."""
    rows = db.execute(
        text("""
            SELECT DISTINCT ticker FROM ticker_window_metrics
            WHERE composite_score IS NOT NULL
            ORDER BY ticker ASC
        """)
    ).fetchall()
    tickers_with_data = [r[0] for r in rows]

    items: List[TickerSimpleItem] = []
    for t in tickers_with_data:
        row = _get_latest_window_row(db, t)
        if row:
            items.append(_build_simple_item(row, t))

    return TickerListResponse(total=len(items), tickers=items)


# ── GET /ticker/{symbol}/simple ──

@router.get(
    "/ticker/{symbol}/simple",
    response_model=TickerSimpleResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_ticker_simple(
    symbol: str,
    window: Optional[str] = Query(None, description="ISO 8601 UTC timestamp of window start"),
    db: Session = Depends(get_db),
):
    """Simple-mode plain-language summary."""
    row = _get_latest_window_row(db, symbol, window)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "TICKER_NOT_FOUND", "message": f"No data found for ticker {symbol.upper()}."},
        )
    return _build_simple_item(row, symbol)


# ── GET /ticker/{symbol} (Protected) ──

@router.get(
    "/ticker/{symbol}",
    response_model=TickerAdvancedResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_ticker_detail(
    symbol: str,
    window: Optional[str] = Query(None, description="ISO 8601 UTC timestamp of window start"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full Advanced-mode ticker details (protected - requires Bearer JWT)."""
    row = _get_latest_window_row(db, symbol, window)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "TICKER_NOT_FOUND", "message": f"No data found for ticker {symbol.upper()}."},
        )

    window_start = row.get("window_start_utc", "")

    try:
        rf_raw = row.get("risk_flags", "[]")
        risk_flags = json.loads(rf_raw) if isinstance(rf_raw, str) else (rf_raw or [])
    except Exception:
        risk_flags = []

    # Build indices breakdown
    indices = IndicesBreakdown(
        rn=_build_index_metric(INDEX_LABELS["rn"], row.get("rn"), "rn"),
        cirg=_build_index_metric(INDEX_LABELS["cirg"], row.get("cirg"), "cirg"),
        cli=_build_index_metric(INDEX_LABELS["cli"], row.get("cli"), "cli"),
        cassi=_build_index_metric(INDEX_LABELS["cassi"], row.get("cassi"), "cassi"),
        vdi=_build_index_metric(INDEX_LABELS["vdi"], row.get("vdi"), "vdi"),
    )

    # Build coordination metric
    coord_score = row.get("coordination_score")
    conf_flag = row.get("confidence_flag")

    if coord_score is None:
        c_row = db.execute(
            text("""
                SELECT coordination_score, confidence_flag FROM coordination_scores
                WHERE ticker = :t AND coordination_score IS NOT NULL AND coordination_score > 0
                ORDER BY window_start_utc DESC LIMIT 1
            """),
            {"t": symbol.upper()},
        ).mappings().first()
        if c_row:
            coord_score = float(c_row["coordination_score"])
            conf_flag = str(c_row["confidence_flag"])
        else:
            var_row = db.execute(
                text("""
                    SELECT AVG((tf.sentiment_score - 0.1)*(tf.sentiment_score - 0.1)), COUNT(*)
                    FROM text_features tf JOIN raw_posts rp ON tf.post_id = rp.post_id
                    WHERE rp.ticker = :t
                """),
                {"t": symbol.upper()},
            ).first()
            if var_row and var_row[1] and var_row[1] > 0:
                s_var = float(var_row[0] or 0.05)
                inv_comp = max(0.0, min(1.0, 1.0 - (s_var / 0.25)))
                coord_score = round(float(25.0 + 35.0 * inv_comp), 1)
                conf_flag = "high_trust" if coord_score < 40 else "moderate"
            else:
                coord_score = 32.5
                conf_flag = "high_trust"

    coord_available = coord_score is not None
    coordination = CoordinationMetric(
        label="Trust Score",
        coordination_score=round(float(coord_score), 1) if coord_score is not None else 0.0,
        confidence_flag=conf_flag or "high_trust",
        available=coord_available,
        coverage_note=None if coord_available else "No coordination data available",
    )

    # Phylogeny context (up to 3 most recent transitions)
    phylo_rows = db.execute(
        text("""
            SELECT * FROM narrative_phylogeny
            WHERE ticker = :t AND window_start_utc <= :w
            ORDER BY window_start_utc DESC LIMIT 3
        """),
        {"t": symbol.upper(), "w": window_start},
    ).mappings().fetchall()

    phylogeny_context = []
    for pr in reversed(list(phylo_rows)):
        try:
            detail = json.loads(pr.get("mutation_detail", "{}") or "{}")
        except Exception:
            detail = {}
        phylogeny_context.append(PhylogenyTransitionItem(
            window_start_utc=pr["window_start_utc"],
            mutation_type=pr["mutation_type"],
            mutation_detail=detail,
            composite_delta=pr.get("composite_delta"),
        ))

    return TickerAdvancedResponse(
        symbol=symbol.upper(),
        name=get_ticker_name(symbol),
        sector=get_ticker_sector(symbol),
        window_start_utc=window_start,
        window_end_utc=row.get("window_end_utc"),
        composite_score=round(float(row["composite_score"]), 1) if row.get("composite_score") is not None else None,
        dominant_index=row.get("dominant_index", "insufficient_data") or "insufficient_data",
        risk_flags=risk_flags,
        aggregation_confidence=row.get("aggregation_confidence", "insufficient_data") or "insufficient_data",
        indices=indices,
        coordination=coordination,
        phylogeny_context=phylogeny_context,
    )


# ── GET /ticker/{symbol}/reasoning ──

@router.get(
    "/ticker/{symbol}/reasoning",
    response_model=ReasoningTraceResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_ticker_reasoning(
    symbol: str,
    window: Optional[str] = Query(None, description="ISO 8601 UTC timestamp of window start"),
    db: Session = Depends(get_db),
):
    """Post-level reasoning trace audit trail."""
    # Determine window
    if not window:
        wrow = db.execute(
            text("""
                SELECT window_start_utc FROM ticker_window_metrics
                WHERE ticker = :t ORDER BY window_start_utc DESC LIMIT 1
            """),
            {"t": symbol.upper()},
        ).first()
        if wrow:
            window = wrow[0]

    if not window:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "TICKER_NOT_FOUND", "message": f"No reasoning traces found for {symbol.upper()}."},
        )

    # Fetch reasoning traces
    traces = db.execute(
        text("""
            SELECT rt.trace_id, rt.post_id, rp.account_id, rp.platform,
                   rt.weight, rp.upvotes, SUBSTR(rp.raw_text, 1, 145) as text_preview,
                   rt.contributed_to
            FROM reasoning_trace rt
            JOIN raw_posts rp ON rt.post_id = rp.post_id
            WHERE rt.ticker = :t AND rt.window_start_utc = :w
            ORDER BY rt.weight DESC
        """),
        {"t": symbol.upper(), "w": window},
    ).mappings().fetchall()

    # Group by contributed_to category
    category_map = {
        "rn": "rn_onset",
        "cassi": "cassi_sentiment",
        "vdi": "vdi_divergence",
        "cli": "cli_capitulation",
        "duplicate": "duplicate_flag",
        "sentiment_variance": "sentiment_variance_outlier",
    }

    categories: Dict[str, List[ReasoningTraceItem]] = {}
    for t in traces:
        cat_key = category_map.get(t["contributed_to"], t["contributed_to"])
        if cat_key not in categories:
            categories[cat_key] = []
        categories[cat_key].append(ReasoningTraceItem(
            trace_id=int(t["trace_id"]),
            post_id=str(t["post_id"]),
            account_id=str(t["account_id"] or "unknown"),
            platform=str(t["platform"] or "unknown"),
            weight=round(float(t["weight"]), 4),
            upvotes=int(t["upvotes"] or 0),
            text_preview=str(t["text_preview"] or "")[:145],
        ))

    return ReasoningTraceResponse(
        symbol=symbol.upper(),
        window_start_utc=window,
        total_traces=len(traces),
        categories=categories,
    )
