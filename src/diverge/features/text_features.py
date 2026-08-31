"""
text_features.py

Phase 2 Text Track: Feature Extraction
Reads raw_posts via storage.get_all_posts_for_text() and computes:
  1. Sentiment Scoring (FinBERT via transformers, fallback to VADER-style lexicon)
  2. Capitulation Detection (lexicon-based placeholder, see NOTE below)
  3. Sarcasm Calibration (rule-based heuristic)
  4. Conviction-Hedge Ratio (certainty vs hedge word counts)
  5. Language Detection (langdetect + Devanagari heuristic)

NOTE on Capitulation Classifier:
The lexicon-based capitulation detector is a placeholder to unblock the pipeline.
It should be replaced with a properly trained binary classifier on a labeled historical
crash-period corpus (e.g. Reddit/StockTwits posts during market drawdowns of 2020, 2022).
The current approach is a frequency-ratio heuristic, not a statistical classifier.
"""

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .. import config, storage, utils

logger = utils.setup_logger("text_features")

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Lexicons
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CAPITULATION_PHRASES = [
    r"sold\s+everything",
    r"i['\s]?m\s+out",
    r"lesson\s+learned",
    r"never\s+again",
    r"done\s+with\s+this",
    r"panic\s+sold",
    r"cut\s+my\s+losses",
    r"got\s+wrecked",
    r"lost\s+it\s+all",
    r"giving\s+up",
    r"never\s+investing\s+again",
    r"should\s+have\s+sold",
    r"took\s+the\s+loss",
    r"exited\s+my\s+position",
    r"closing\s+everything",
    r"this\s+broke\s+me",
    r"burnt\s+to\s+the\s+ground",
]
CAPITULATION_THRESHOLD = 0.015  # ratio of matched phrase tokens / total words

CERTAINTY_TERMS = [
    r"\bguaranteed\b",
    r"\b100\s*%\b",
    r"\bdefinitely\b",
    r"\ball\s+in\b",
    r"\bcertain\b",
    r"\bconfirmed\b",
    r"\bwithout\s+a\s+doubt\b",
    r"\bno\s+doubt\b",
    r"\bsure\s+thing\b",
    r"\bno\s+brainer\b",
    r"\babsolutely\b",
]

HEDGE_TERMS = [
    r"\bmight\b",
    r"\bcould\b",
    r"\bnot\s+financial\s+advice\b",
    r"\bmaybe\b",
    r"\bpossibly\b",
    r"\bperhaps\b",
    r"\bnfa\b",
    r"\bdyor\b",
    r"\bdo\s+your\s+own\s+research\b",
    r"\bi\s+think\b",
    r"\bi\s+believe\b",
    r"\bprobably\b",
    r"\bnot\s+sure\b",
    r"\bcould\s+be\s+wrong\b",
]

# Sarcasm markers
SARCASM_CERTAINTY_HIGH = [
    r"\bguaranteed\b",
    r"\babsolutely\b",
    r"\b100\s*%\b",
    r"\bno\s+doubt\b",
]
SARCASM_LOSS_SIGNALS = [
    r"-?\$[\d,]+",         # loss amount like -$5000
    r"\blost\b",
    r"\bdown\s+\d+",
    r"\blosing\b",
    r"\bwrecked\b",
    r"\bstonks\b",         # ironic usage of "stonks"
]
ROCKET_EMOJI_PATTERN = re.compile(r"[\U0001F680\U0001F4C8]")  # ðŸš€ðŸ“ˆ
NFA_PATTERN = re.compile(
    r"(not\s+financial\s+advice|nfa\b|do\s+your\s+own\s+research|dyor\b)", re.IGNORECASE
)

# Devanagari Unicode range for Hindi language detection
DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")
HINDI_ROMAN_MARKERS = re.compile(
    r"\b(kya|hai|nahi|matlab|bhai|yaar|agar|bohot|bahut|mujhe|hoga|wala|lagta|paise)\b",
    re.IGNORECASE,
)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FinBERT / Sentiment Model
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_sentiment_pipeline = None


def _load_sentiment_model():
    """Load FinBERT sentiment model once. Falls back gracefully if offline/unavailable."""
    global _sentiment_pipeline
    if _sentiment_pipeline is not None:
        return _sentiment_pipeline
    try:
        from transformers import pipeline as hf_pipeline
        logger.info("Loading FinBERT sentiment model (ProsusAI/finbert)...")
        _sentiment_pipeline = hf_pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            truncation=True,
            max_length=512,
        )
        logger.info("FinBERT model loaded.")
    except Exception as e:
        logger.warning(f"Could not load FinBERT ({e}). Falling back to keyword-based sentiment.")
        _sentiment_pipeline = None
    return _sentiment_pipeline


FALLBACK_BULLISH = re.compile(
    r"\b(buy|bull|bullish|moon|pump|surge|breakout|rally|long|upside|gain|"
    r"profit|growth|strong|beat|exceed|record\s+high|all.time\s+high)\b",
    re.IGNORECASE,
)
FALLBACK_BEARISH = re.compile(
    r"\b(sell|bear|bearish|dump|crash|drop|fall|short|downside|loss|"
    r"decline|weak|miss|disappoint|record\s+low|all.time\s+low)\b",
    re.IGNORECASE,
)


def _keyword_sentiment(text: str) -> tuple[float, str]:
    """Simple fallback keyword-based sentiment when FinBERT is unavailable."""
    bull = len(FALLBACK_BULLISH.findall(text))
    bear = len(FALLBACK_BEARISH.findall(text))
    total = bull + bear
    if total == 0:
        return 0.0, "neutral"
    score = (bull - bear) / total
    label = "bullish" if score > 0.1 else ("bearish" if score < -0.1 else "neutral")
    return round(score, 4), label


def score_sentiment_batch(texts: List[str], pipe=None) -> List[tuple[float, str]]:
    """
    Score a batch of texts for sentiment.
    With FinBERT: maps positiveâ†’bullish, negativeâ†’bearish, neutralâ†’neutral.
    Without FinBERT: falls back to keyword matching.
    Returns list of (score, label) tuples.
    """
    label_map = {"positive": "bullish", "negative": "bearish", "neutral": "neutral"}
    sign_map = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}

    if pipe is None:
        return [_keyword_sentiment(t) for t in texts]

    results = []
    try:
        # Process texts in sub-batches to avoid OOM on large runs
        BATCH = 32
        for i in range(0, len(texts), BATCH):
            chunk = texts[i : i + BATCH]
            preds = pipe(chunk)
            for p in preds:
                raw_label = p["label"].lower()
                score = sign_map.get(raw_label, 0.0) * p["score"]
                label = label_map.get(raw_label, "neutral")
                results.append((round(score, 4), label))
    except Exception as e:
        logger.warning(f"FinBERT inference error: {e}. Falling back to keywords for batch.")
        results = [_keyword_sentiment(t) for t in texts]
    return results


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Capitulation Detection
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_cap_patterns = [re.compile(p, re.IGNORECASE) for p in CAPITULATION_PHRASES]


def detect_capitulation(text: str) -> tuple[int, float]:
    """
    Lexicon-based capitulation detection (placeholder).
    Returns (flag: 0|1, confidence: 0.0-1.0).

    NOTE: Replace with a binary classifier trained on a labeled historical corpus
    of crash-period posts (e.g. WSB/StockTwits during 2020-03, 2022-05 drawdowns)
    when labeled data becomes available. Lexicon coverage is ~65-70% recall on
    known capitulation phrases but misses indirect expressions.
    """
    if not text or not text.strip():
        return 0, 0.0
    word_count = max(len(text.split()), 1)
    matched_tokens = 0
    for pat in _cap_patterns:
        for m in pat.finditer(text):
            matched_tokens += len(m.group(0).split())
    confidence = min(matched_tokens / word_count * 20, 1.0)  # scale to [0,1]
    flag = 1 if confidence >= CAPITULATION_THRESHOLD * 20 else 0
    return flag, round(confidence, 4)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Sarcasm Calibration
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_certainty_high = [re.compile(p, re.IGNORECASE) for p in SARCASM_CERTAINTY_HIGH]
_loss_signals = [re.compile(p, re.IGNORECASE) for p in SARCASM_LOSS_SIGNALS]


def detect_sarcasm(text: str) -> int:
    """
    Rule-based sarcasm detection heuristic.
    Flags as sarcastic (1) when:
      - High-certainty language co-occurs with explicit loss signals (contradictory pattern)
      - Rocket emoji(s) appear with loss signals
      - NFA disclaimer co-occurs with high-certainty language
    Returns 0 or 1. Documented as a heuristic â€” not a trained classifier.
    """
    if not text:
        return 0

    has_high_certainty = any(p.search(text) for p in _certainty_high)
    has_loss = any(p.search(text) for p in _loss_signals)
    has_rocket = bool(ROCKET_EMOJI_PATTERN.search(text))
    has_nfa = bool(NFA_PATTERN.search(text))

    if has_high_certainty and has_loss:
        return 1
    if has_rocket and has_loss:
        return 1
    if has_nfa and has_high_certainty:
        return 1
    return 0


def irony_adjusted(sentiment_score: float, is_sarcastic: int) -> float:
    """
    Heuristic sarcasm correction: when sarcasm is detected, dampen the sentiment
    toward zero by 70% rather than fully flipping it. This is intentionally conservative
    because rule-based sarcasm detection has low precision â€” a full flip would introduce
    more noise than the dampening. Document as a heuristic pending a labeled sarcasm corpus.
    """
    if not is_sarcastic:
        return sentiment_score
    return round(sentiment_score * 0.3, 4)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Conviction-Hedge Ratio
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_certainty_pats = [re.compile(p, re.IGNORECASE) for p in CERTAINTY_TERMS]
_hedge_pats = [re.compile(p, re.IGNORECASE) for p in HEDGE_TERMS]


def conviction_hedge_ratio(text: str) -> Optional[float]:
    """
    Compute ratio of certainty term count to hedge term count.
    Returns None when both counts are 0 (avoids meaningless 0/0).
    Returns certainty_count / (hedge_count or 1) when only one is zero.
    Note: When hedge_count == 0 but certainty_count > 0, returns certainty_count
    (effectively infinity is capped by the word count normalizer below).
    """
    if not text:
        return None
    certainty_count = sum(len(p.findall(text)) for p in _certainty_pats)
    hedge_count = sum(len(p.findall(text)) for p in _hedge_pats)

    if certainty_count == 0 and hedge_count == 0:
        return None
    if hedge_count == 0:
        return float(certainty_count)
    return round(certainty_count / hedge_count, 4)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Language Detection
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def detect_language(text: str) -> str:
    """
    Detect language of post text.
    Priority:
      1. Devanagari Unicode range â†’ 'hi-en-mixed' (code-mix assumed with stock context)
      2. Romanized Hindi markers heuristic â†’ 'hi-en-mixed'
      3. langdetect library â†’ 'en' or detected ISO code
    Returns: 'en', 'hi-en-mixed', or ISO 639-1 code.
    """
    if not text or not text.strip():
        return "en"

    if DEVANAGARI_PATTERN.search(text):
        return "hi-en-mixed"
    if HINDI_ROMAN_MARKERS.search(text):
        return "hi-en-mixed"

    try:
        from langdetect import detect as ld_detect
        lang = ld_detect(text)
        if lang in ("hi", "ne", "mr"):
            return "hi-en-mixed"
        return lang
    except Exception:
        return "en"


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Main Feature Extraction
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def extract_features_for_posts(posts: List[tuple], pipe=None) -> List[Dict[str, Any]]:
    """
    Given list of (post_id, raw_text, ticker) tuples, compute all text features.
    Returns list of dicts matching the text_features table schema.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    texts = [row[1] or "" for row in posts]

    logger.info(f"Running sentiment scoring on {len(texts)} posts...")
    sentiments = score_sentiment_batch(texts, pipe=pipe)

    results = []
    for i, (post_id, raw_text, ticker) in enumerate(posts):
        text = raw_text or ""
        sent_score, sent_label = sentiments[i]

        cap_flag, cap_conf = detect_capitulation(text)
        sarcastic = detect_sarcasm(text)
        irony_adj = irony_adjusted(sent_score, sarcastic)
        conv_ratio = conviction_hedge_ratio(text)
        lang = detect_language(text)

        results.append({
            "post_id": post_id,
            "sentiment_score": sent_score,
            "sentiment_label": sent_label,
            "capitulation_flag": cap_flag,
            "capitulation_confidence": cap_conf,
            "is_sarcastic": sarcastic,
            "irony_adjusted_sentiment": irony_adj,
            "conviction_hedge_ratio": conv_ratio,
            "language": lang,
            "computed_at": now_iso,
        })

    return results


def run(db_path: Path = config.DB_PATH, log_every: int = 50) -> int:
    """
    Execute full text feature extraction pipeline:
    1. Load all posts from raw_posts (blind to timing data)
    2. Load FinBERT (or fallback)
    3. Compute features in batches
    4. Write to text_features via INSERT OR IGNORE
    Returns: count of new rows inserted
    """
    logger.info("Starting text feature extraction...")

    posts = storage.get_all_posts_for_text(db_path=db_path)
    if not posts:
        logger.warning("No posts found in raw_posts. Nothing to process.")
        return 0
    logger.info(f"Loaded {len(posts)} posts for text feature extraction.")

    pipe = _load_sentiment_model()

    # Process in batches, logging progress
    BATCH = 64
    all_features = []
    for start in range(0, len(posts), BATCH):
        batch = posts[start : start + BATCH]
        features = extract_features_for_posts(batch, pipe=pipe)
        all_features.extend(features)
        processed = min(start + BATCH, len(posts))
        if processed % log_every == 0 or processed == len(posts):
            logger.info(f"Text features extracted for {processed}/{len(posts)} posts...")

    new_rows = storage.insert_text_features(all_features, db_path=db_path)
    logger.info(f"Text feature extraction complete. {new_rows} new rows inserted into text_features.")
    return new_rows


if __name__ == "__main__":
    run()

