"""
main.py

Root launcher delegating to diverge.scrapers.run_phase1.
"""
from diverge.scrapers import run_phase1

if __name__ == "__main__":
    run_phase1.run_pipeline()
