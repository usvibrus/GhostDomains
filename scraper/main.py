"""GhostDomains — Main Scraper Orchestrator"""
import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scraper.config import Config
from scraper.db import (
    init_db, save_channel, save_domain, save_metrics,
    get_domains_to_recheck, channel_exists, get_channels_to_scrape
)
from scraper.youtube import search_channels, fetch_channel_details, SEARCH_QUERIES
from scraper.external import fetch_expired_domain_feeds
from scraper.extractor import extract_domains_from_text, extract_tld
from scraper.checker import full_check
from scraper.metrics import score_domain, get_pagerank

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('ghostdomains')


def run_youtube_pipeline(max_queries=5):
    """YouTube discovery: search channels → extract URLs → check → score."""
    if not Config.has_youtube():
        logger.warning("YouTube API key not set. Skipping YouTube pipeline.")
        return

    logger.info("=== YOUTUBE PIPELINE START ===")
    total_domains_found = 0

    for query in SEARCH_QUERIES[:max_queries]:
        logger.info(f"Searching YouTube for: '{query}'")
        channel_ids, _ = search_channels(query=query, max_results=50)

        # Filter out already-known channels
        new_ids = [cid for cid in channel_ids if not channel_exists(cid)]
        if not new_ids:
            logger.info(f"  No new channels for '{query}'")
            continue

        # Fetch details
        channels = fetch_channel_details(new_ids)

        for ch in channels:
            save_channel(ch)
            # Extract domains from description
            domains = extract_domains_from_text(ch.get('description', ''))
            logger.info(f"  Channel '{ch['name']}': {len(domains)} domains found")

            for domain_name in domains:
                total_domains_found += 1
                _process_domain(domain_name, 'youtube', ch['channel_id'])

    logger.info(f"=== YOUTUBE PIPELINE DONE: {total_domains_found} domains processed ===")


def run_external_pipeline():
    """External discovery: feeds, CT logs → check → score."""
    logger.info("=== EXTERNAL PIPELINE START ===")

    domains = fetch_expired_domain_feeds()
    logger.info(f"External sources returned {len(domains)} raw domains")

    for domain_name in domains:
        _process_domain(domain_name, 'feed')

    logger.info(f"=== EXTERNAL PIPELINE DONE: {len(domains)} domains processed ===")


def run_recheck():
    """Re-check existing domains that haven't been verified recently."""
    logger.info("=== RECHECK PIPELINE START ===")

    domains = get_domains_to_recheck(hours=Config.RECHECK_INTERVAL_HOURS)
    logger.info(f"Rechecking {len(domains)} domains")

    for d in domains:
        _process_domain(d['domain'], d.get('discovery_source', 'manual'), recheck=True)

    logger.info(f"=== RECHECK DONE ===")


def _process_domain(domain_name, source='manual', channel_id=None, recheck=False):
    """Process a single domain: check status → score → save."""
    try:
        # Check WHOIS/DNS/HTTP
        check_result = full_check(domain_name, delay=Config.WHOIS_DELAY)

        # Save domain
        domain_data = {
            'domain': domain_name,
            'tld': extract_tld(domain_name),
            'discovery_source': source,
            'source_channel_id': channel_id,
            **check_result,
        }
        domain_id = save_domain(domain_data)

        # Score the domain
        if domain_id:
            metrics = score_domain(domain_name)
            save_metrics(domain_id, metrics)
            label = "EXPIRED" if check_result.get('is_expired') else "active"
            logger.info(f"  ✓ {domain_name} [{label}] score={metrics['composite_score']}")

    except Exception as e:
        logger.error(f"  ✗ Error processing {domain_name}: {e}")


def main():
    parser = argparse.ArgumentParser(description='GhostDomains Scraper')
    parser.add_argument('--mode', choices=['youtube', 'external', 'full', 'recheck'],
                        default='full', help='Pipeline mode')
    parser.add_argument('--max-queries', type=int, default=5,
                        help='Max YouTube search queries per run')
    args = parser.parse_args()

    # Initialize database
    init_db()
    logger.info(f"Running in mode: {args.mode}")

    if args.mode == 'youtube':
        run_youtube_pipeline(max_queries=args.max_queries)
    elif args.mode == 'external':
        run_external_pipeline()
    elif args.mode == 'full':
        run_youtube_pipeline(max_queries=args.max_queries)
        run_external_pipeline()
    elif args.mode == 'recheck':
        run_recheck()

    logger.info("Pipeline complete!")


if __name__ == '__main__':
    main()
