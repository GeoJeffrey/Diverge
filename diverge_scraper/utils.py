"""
utils.py

Shared utility helpers for the Diverge scraper package:
- match_ticker(text): Match ticker regex synonyms against input text.
- to_iso_utc(val): Convert timestamp / datetime to ISO 8601 UTC string.
- stable_id(*parts): Generate deterministic SHA-256 hash for record IDs.
- setup_logger(name): Configure structured logger for scrapers.
- is_allowed_by_robots(url): Check robots.txt permissions prior to scraping.
"""

import hashlib
import logging
import re
import urllib.parse
import urllib.robotparser
from datetime import datetime, timezone
from typing import Any, Optional

from . import config


def match_ticker(text: str) -> Optional[str]:
    """
    Return the first ticker symbol whose regex pattern matches the given text,
    or None if no patterns match.
    """
    if not text:
        return None
    text_lower = text.lower()
    for ticker, patterns in config.TICKERS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return ticker
    return None


def to_iso_utc(val: Any) -> str:
    """
    Convert a Unix timestamp (int/float), ISO string, or datetime object
    into a standardized ISO 8601 UTC string.
    """
    if val is None:
        return datetime.now(timezone.utc).isoformat()

    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc).isoformat()

    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        else:
            val = val.astimezone(timezone.utc)
        return val.isoformat()

    if isinstance(val, str):
        val = val.strip()
        if not val:
            return datetime.now(timezone.utc).isoformat()
        try:
            # Handle ISO string or timestamp string
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.isoformat()
        except ValueError:
            pass

    return str(val)


def stable_id(*parts: Any) -> str:
    """
    Generate a deterministic SHA-256 hex string ID from provided string parts.
    Useful when scraped entries lack a clean unique ID (e.g. RSS entries or web elements).
    """
    combined = "_".join(str(p) for p in parts if p is not None)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def setup_logger(name: str) -> logging.Logger:
    """
    Configure and return a standard Logger instance for scraper modules,
    outputting to both console and file (diverge_scraper.log).
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        try:
            fh = logging.FileHandler(config.LOG_FILE_PATH, encoding="utf-8")
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            pass

    return logger


def is_allowed_by_robots(url: str, user_agent: str = config.USER_AGENT) -> bool:
    """
    Check if scraping target URL is allowed by the site's robots.txt.
    Returns True if allowed or if robots.txt cannot be fetched/parsed.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        # If robots.txt fetch fails or network fails, assume True but log gracefully
        return True
