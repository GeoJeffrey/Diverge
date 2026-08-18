"""
config.py

Central configuration for Diverge Phase 1 Scraper module.
Includes tracked tickers with regex synonym lists, source URLs,
rate-limit delays, user agent header, and database retention settings.
"""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "diverge_raw.db"
LOG_FILE_PATH = BASE_DIR / "diverge_scraper.log"

# Central Ticker Configuration
# Key: Standardized Ticker Symbol
# Value: List of regex patterns (case-insensitive) matching company names, synonyms, or symbols
TICKERS = {
    "TATASTEEL": [
        r"\btata\s*steel\b",
        r"\btatasteel\b",
    ],
    "RELIANCE": [
        r"\breliance\b",
        r"\bril\b",
        r"\breliance\s*industries\b",
    ],
    "INFY": [
        r"\binfosys\b",
        r"\binfy\b",
    ],
    "TCS": [
        r"\btcs\b",
        r"\btata\s*consultancy\b",
    ],
    "HDFCBANK": [
        r"\bhdfc\s*bank\b",
        r"\bhdfc\b",
    ],
    "ICICIBANK": [
        r"\bicici\s*bank\b",
        r"\bicici\b",
    ],
    "SBIN": [
        r"\bsbi\b",
        r"\bstate\s*bank\s*of\s*india\b",
        r"\bsbin\b",
    ],
    "BHARTIARTL": [
        r"\bharti\s*airtel\b",
        r"\bairtel\b",
    ],
    "ITC": [
        r"\bitc\b",
        r"\bitc\s*limited\b",
    ],
    "LT": [
        r"\blarsen\s*(&|\+)?\s*toubro\b",
        r"\bl&t\b",
    ],
    "WIPRO": [
        r"\bwipro\b",
    ],
    "AAPL": [
        r"\baapl\b",
        r"\bapple\s*inc\b",
        r"\bapple\s*stock\b",
    ],
    "TSLA": [
        r"\btsla\b",
        r"\btesla\b",
    ],
    "NVDA": [
        r"\bnvda\b",
        r"\bnvidia\b",
    ],
    "MSFT": [
        r"\bmsft\b",
        r"\bmicrosoft\b",
    ],
    "AMZN": [
        r"\bamzn\b",
        r"\bamazon\b",
    ],
}

# Reddit Configuration
REDDIT_SUBREDDITS = [
    "IndianStreetBets",
    "IndiaInvestments",
    "wallstreetbets",
    "stocks",
    "investing",
    "stockmarket",
    "DalalStreetBets",
    "finance",
]
REDDIT_POST_LIMIT = 100
REDDIT_DELAY_RANGE = (2.0, 4.0)

# StockTwits Configuration
STOCKTWITS_SYMBOLS = [
    "INFY",
    "TCS",
    "AAPL",
    "TSLA",
    "NVDA",
    "MSFT",
    "AMZN",
    "RELIANCE",
    "HDFCBANK",
]
STOCKTWITS_DELAY = 2.0

# Telegram Configuration
TELEGRAM_CHANNELS = [
    "IndianStreetBets",
    "StockMarketIndia",
    "dalalstreetjournal",
    "nifty50trader",
]
TELEGRAM_DELAY = 2.0

# RSS News Feeds Configuration
RSS_FEEDS = [
    {
        "name": "Moneycontrol Top News",
        "url": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    },
    {
        "name": "Economic Times Markets",
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms",
    },
    {
        "name": "Reuters Business",
        "url": "https://feeds.feedburner.com/reuters/INbusinessNews",
    },
    {
        "name": "Business Standard Market",
        "url": "https://www.business-standard.com/rss/markets-106.rss",
    },
    {
        "name": "NDTV Profit",
        "url": "https://feeds.feedburner.com/ndtvprofit-latest",
    },
]
RSS_DELAY = 1.0

# Google Trends Configuration
TRENDS_KEYWORDS = ["TATASTEEL", "RELIANCE", "INFY", "TCS", "HDFCBANK", "AAPL", "TSLA", "NVDA"]
TRENDS_GEO = "IN"
TRENDS_TIMEFRAME = "today 1-m"
TRENDS_DELAY = 2.0

# General HTTP Configuration
USER_AGENT = "DivergeResearchBot/0.1 (student project; narrative-sentiment research)"

# Data Retention
RETENTION_DAYS = 90
