"""
main.py

Root entrypoint for running the Diverge Phase 1 data collection pipeline.
Delegates to diverge_scraper.main.run_pipeline().
"""

from diverge_scraper.main import run_pipeline

if __name__ == "__main__":
    run_pipeline()
