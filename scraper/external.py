import logging
import requests
import time
import re

logger = logging.getLogger(__name__)


def fetch_expired_domain_feeds():
    """Fetch expired domains from public feeds. Returns list of domain strings."""
    domains = set()
    domains.update(_fetch_drop_lists())
    logger.info(f"External sources returned {len(domains)} domains total")
    return list(domains)


def _fetch_drop_lists():
    """Fetch from public domain drop/delete lists."""
    domains = set()
    try:
        resp = requests.get(
            'https://crt.sh/?output=json&expired=true&limit=100',
            timeout=15, headers={'User-Agent': 'GhostDomains/1.0'},
        )
        if resp.status_code == 200:
            for entry in resp.json():
                name = entry.get('common_name', '')
                if name and '.' in name and not name.startswith('*'):
                    domains.add(name.lower())
            logger.info(f"CT logs: found {len(domains)} domains")
    except Exception as e:
        logger.debug(f"CT log fetch error: {e}")
    return domains
