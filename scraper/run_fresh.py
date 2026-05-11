"""Run scraper with fresh search queries."""
import sys, os, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scraper.config import Config
from scraper.db import init_db, save_channel, save_domain, save_metrics, channel_exists
from scraper.youtube import search_channels, fetch_channel_details
from scraper.extractor import extract_domains_from_text, extract_tld
from scraper.checker import full_check
from scraper.metrics import score_domain

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('ghostdomains')

init_db()
queries = ['photography portfolio', 'web design agency', 'digital marketing blog', 'podcast show', 'gaming streamer']

for q in queries:
    logger.info(f'Searching: {q}')
    ids, _ = search_channels(query=q, max_results=50)
    new_ids = [c for c in ids if not channel_exists(c)]
    if not new_ids:
        logger.info(f'  No new channels')
        continue
    channels = fetch_channel_details(new_ids)
    for ch in channels:
        save_channel(ch)
        domains = extract_domains_from_text(ch.get('description', ''))
        if domains:
            name = ch.get('name', 'Unknown')
            logger.info(f'  {name}: {len(domains)} domains')
            for d in domains:
                try:
                    check = full_check(d, delay=0.5)
                    dd = {
                        'domain': d, 'tld': extract_tld(d),
                        'discovery_source': 'youtube',
                        'source_channel_id': ch['channel_id'],
                        **check,
                    }
                    did = save_domain(dd)
                    if did:
                        m = score_domain(d)
                        save_metrics(did, m)
                        label = 'EXPIRED' if check.get('is_expired') else 'active'
                        logger.info(f'    {d} [{label}] score={m["composite_score"]}')
                except Exception as e:
                    logger.error(f'    Error: {d} - {e}')

logger.info('Done!')
