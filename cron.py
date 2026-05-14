#!/usr/bin/env python
"""
GhostDomains Cron Entry Point
Runs the full scraper pipeline — designed to be called by Railway Cron.
Set SCRAPER_MODE env var to control what runs (default: full).
"""
import os
import sys
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('ghostdomains.cron')

sys.path.insert(0, os.path.dirname(__file__))

def main():
    mode = os.getenv('SCRAPER_MODE', 'full')
    logger.info(f"=== GhostDomains Cron Job Starting ===")
    logger.info(f"Time: {datetime.now(timezone.utc).isoformat()} UTC")
    logger.info(f"Mode: {mode}")
    logger.info(f"DB: {'PostgreSQL' if os.getenv('DATABASE_URL','').startswith('postgres') else 'SQLite'}")

    from scraper.db import init_db
    init_db()

    if mode in ('youtube', 'full'):
        logger.info("--- Starting YouTube pipeline ---")
        from scraper.main import run_youtube_pipeline
        run_youtube_pipeline()

    if mode in ('external', 'full'):
        logger.info("--- Starting External pipeline ---")
        from scraper.main import run_external_pipeline
        run_external_pipeline()

    if mode == 'recheck':
        logger.info("--- Starting Recheck pipeline ---")
        from scraper.main import run_recheck
        run_recheck()

    logger.info("=== Cron Job Complete ===")

if __name__ == '__main__':
    main()
