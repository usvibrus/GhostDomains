#!/usr/bin/env python
"""
GhostDomains Cron Entry Point
Runs the full scraper pipeline — designed to be called by Railway Cron.
Set SCRAPER_MODE env var to control what runs (default: full).
"""
import os
import sys
import logging
from datetime import datetime

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
    logger.info(f"Time: {datetime.utcnow().isoformat()} UTC")
    logger.info(f"Mode: {mode}")
    logger.info(f"DB: {'PostgreSQL' if os.getenv('DATABASE_URL','').startswith('postgres') else 'SQLite'}")

    from scraper.db import init_db
    init_db()

    if mode in ('youtube', 'full'):
        logger.info("--- Starting YouTube pipeline ---")
        from scraper.youtube import run_youtube_pipeline
        run_youtube_pipeline()

    if mode in ('external', 'full'):
        logger.info("--- Starting External pipeline ---")
        from scraper.external import run_external_pipeline
        run_external_pipeline()

    if mode == 'recheck':
        logger.info("--- Starting Recheck pipeline ---")
        from scraper.checker import recheck_domains
        recheck_domains()

    logger.info("=== Cron Job Complete ===")

if __name__ == '__main__':
    main()
