"""
main.py

Main orchestrator for the Diverge Phase 1 data collection module.
Executes scrapers sequentially in order:
  1. Google Trends
  2. RSS news feeds
  3. StockTwits public stream
  4. Telegram public channel preview
  5. Reddit public JSON

Each scraper execution is wrapped in try/except blocks so failure in one source
never halts execution of remaining scrapers. Purges old raw_text according to
the configured retention policy and prints a summary of database contents.
"""

from . import (
    config,
    reddit_noapi_scraper,
    rss_news_scraper,
    stocktwits_noapi_scraper,
    storage,
    telegram_noapi_scraper,
    trends_scraper,
    utils,
)

logger = utils.setup_logger("main_orchestrator")


def print_summary() -> None:
    """Print database row counts per platform and top 5 recent posts."""
    print("\n" + "=" * 60)
    print("DIVERGE RAW DATA STORAGE SUMMARY")
    print("=" * 60)

    counts = storage.count_by_platform()
    if not counts:
        print("No records stored in database yet.")
    else:
        print("Row counts per platform:")
        for platform, count in sorted(counts.items()):
            print(f"  - {platform}: {count} rows")

    recent = storage.recent_posts(limit=5)
    if recent:
        print("\n5 Most Recently Scraped Rows:")
        for platform, ticker, account, ts, text in recent:
            preview = (text[:80] + "...") if len(text) > 80 else text
            preview_clean = preview.replace("\n", " ")
            print(f"  [{platform}] {ticker} | {account} | {ts}")
            print(f"      \"{preview_clean}\"")
    print("=" * 60 + "\n")


def run_pipeline() -> None:
    """Run all scraper modules sequentially in required order."""
    logger.info("Starting Diverge Phase 1 data collection pipeline...")

    # 1. Google Trends
    logger.info("--- [1/5] Executing Google Trends Scraper ---")
    try:
        trends_scraper.run()
    except Exception as e:
        logger.error(f"Google Trends scraper failed: {e}")

    # 2. RSS News Feeds
    logger.info("--- [2/5] Executing RSS News Feeds Scraper ---")
    try:
        rss_news_scraper.run()
    except Exception as e:
        logger.error(f"RSS news feeds scraper failed: {e}")

    # 3. StockTwits Streams
    logger.info("--- [3/5] Executing StockTwits Public Streams Scraper ---")
    try:
        stocktwits_noapi_scraper.run()
    except Exception as e:
        logger.error(f"StockTwits scraper failed: {e}")

    # 4. Telegram Channel Previews
    logger.info("--- [4/5] Executing Telegram Public Previews Scraper ---")
    try:
        telegram_noapi_scraper.run()
    except Exception as e:
        logger.error(f"Telegram preview scraper failed: {e}")

    # 5. Reddit Public JSON
    logger.info("--- [5/5] Executing Reddit Public JSON Scraper ---")
    try:
        reddit_noapi_scraper.run()
    except Exception as e:
        logger.error(f"Reddit JSON scraper failed: {e}")

    # Data Retention Purge
    logger.info(f"Purging raw text older than {config.RETENTION_DAYS} days...")
    try:
        purged = storage.purge_old_text(config.RETENTION_DAYS)
        logger.info(f"Purged raw text for {purged} old records.")
    except Exception as e:
        logger.error(f"Data retention purge failed: {e}")

    # Print summary report
    print_summary()


if __name__ == "__main__":
    run_pipeline()
