"""
ticker_metadata.py

Canonical ticker metadata mapping symbols to human-readable company names and sectors.
Used by API endpoints to enrich responses per the frozen openapi.json contract.
"""

TICKER_INFO = {
    "TATASTEEL": {"name": "Tata Steel Ltd.", "sector": "Basic Materials"},
    "RELIANCE": {"name": "Reliance Industries Ltd.", "sector": "Energy"},
    "INFY": {"name": "Infosys Ltd.", "sector": "Information Technology"},
    "TCS": {"name": "Tata Consultancy Services Ltd.", "sector": "Information Technology"},
    "HDFCBANK": {"name": "HDFC Bank Ltd.", "sector": "Financial Services"},
    "ICICIBANK": {"name": "ICICI Bank Ltd.", "sector": "Financial Services"},
    "SBIN": {"name": "State Bank of India", "sector": "Financial Services"},
    "BHARTIARTL": {"name": "Bharti Airtel Ltd.", "sector": "Consumer Discretionary"},
    "ITC": {"name": "ITC Ltd.", "sector": "Consumer Goods"},
    "LT": {"name": "Larsen & Toubro Ltd.", "sector": "Conglomerate"},
    "WIPRO": {"name": "Wipro Ltd.", "sector": "Information Technology"},
    "AAPL": {"name": "Apple Inc.", "sector": "Information Technology"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Automotive"},
    "NVDA": {"name": "NVIDIA Corp.", "sector": "Information Technology"},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Information Technology"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
}


def get_ticker_name(symbol: str) -> str:
    return TICKER_INFO.get(symbol.upper(), {}).get("name", symbol.upper())


def get_ticker_sector(symbol: str) -> str:
    return TICKER_INFO.get(symbol.upper(), {}).get("sector", "Other")
