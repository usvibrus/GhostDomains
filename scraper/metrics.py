import math
import time
import logging
import requests
from datetime import datetime

from scraper.config import Config

logger = logging.getLogger(__name__)


def get_pagerank(domains, batch_size=100):
    """
    Get Open PageRank scores for a batch of domains.
    Returns dict: {domain: score}
    Maps to Domain Authority (DA) in the dashboard.
    """
    if not domains:
        return {}

    results = {}

    for i in range(0, len(domains), batch_size):
        batch = domains[i:i + batch_size]
        try:
            resp = requests.get(
                'https://openpagerank.com/api/v1.0/getPageRank',
                params=[('domains[]', d) for d in batch],
                headers={'API-OPR': Config.OPEN_PAGERANK_KEY} if Config.OPEN_PAGERANK_KEY else {},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('response', []):
                    domain = item.get('domain', '')
                    rank = item.get('page_rank_decimal', 0)
                    results[domain] = float(rank) if rank else 0.0
            else:
                logger.warning(f"PageRank API returned {resp.status_code}")
        except Exception as e:
            logger.error(f"PageRank API error: {e}")

        time.sleep(0.5)

    return results


def wayback_check(domain, delay=0.5):
    """
    Query Wayback Machine CDX API for snapshot count and earliest snapshot date.
    Returns dict: {snapshots: int, archive_age_days: int}
    """
    result = {'snapshots': 0, 'archive_age_days': 0}

    try:
        # Get snapshot count using CDX API
        resp = requests.get(
            'https://web.archive.org/cdx/search/cdx',
            params={
                'url': domain,
                'output': 'json',
                'fl': 'timestamp',
                'limit': 5000,
                'collapse': 'timestamp:8',  # Collapse by day
            },
            timeout=15,
            headers={'User-Agent': 'GhostDomains/1.0'},
        )

        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 1:  # First row is headers
                result['snapshots'] = len(data) - 1
                # Earliest snapshot
                earliest = data[1][0]  # timestamp string like "20150301120000"
                try:
                    earliest_date = datetime.strptime(earliest[:8], '%Y%m%d')
                    result['archive_age_days'] = (datetime.utcnow() - earliest_date).days
                except ValueError:
                    pass
    except Exception as e:
        logger.debug(f"Wayback check failed for {domain}: {e}")

    time.sleep(delay)
    return result


def safe_browsing_check(domains):
    """
    Check domains against Google Safe Browsing API.
    Returns dict: {domain: True/False} (True = safe).
    """
    if not Config.has_safe_browsing() or not domains:
        return {d: True for d in domains}  # Assume safe if no API key

    results = {d: True for d in domains}

    try:
        payload = {
            'client': {'clientId': 'ghostdomains', 'clientVersion': '1.0'},
            'threatInfo': {
                'threatTypes': ['MALWARE', 'SOCIAL_ENGINEERING', 'UNWANTED_SOFTWARE'],
                'platformTypes': ['ANY_PLATFORM'],
                'threatEntryTypes': ['URL'],
                'threatEntries': [{'url': f'http://{d}'} for d in domains],
            }
        }

        resp = requests.post(
            f'https://safebrowsing.googleapis.com/v4/threatMatches:find?key={Config.GOOGLE_SAFE_BROWSING_KEY}',
            json=payload,
            timeout=10,
        )

        if resp.status_code == 200:
            data = resp.json()
            for match in data.get('matches', []):
                url = match.get('threat', {}).get('url', '')
                domain = url.replace('http://', '').replace('https://', '').strip('/')
                if domain in results:
                    results[domain] = False  # Unsafe
    except Exception as e:
        logger.error(f"Safe Browsing API error: {e}")

    return results


def compute_score(domain_authority, page_authority, trust_flow, backlinks, wayback_snapshots, google_safe):
    """
    Compute composite score (0–100) from all metrics.
    Normalized and weighted formula.
    """
    # Normalize each component to 0–10
    da_norm = min(domain_authority / 10, 10)          # DA 0-100 → 0-10
    pa_norm = min(page_authority / 10, 10)            # PA 0-100 → 0-10
    tf_norm = min(trust_flow / 10, 10)                # TF 0-100 → 0-10
    bl_norm = min(math.log10(backlinks + 1) / 5 * 10, 10)  # Log scale
    wb_norm = min(wayback_snapshots / 500 * 10, 10)   # 500+ = max

    # Safety penalty
    safe_pen = 0 if google_safe else -30

    # Weighted sum (weights sum to 10, so result is 0-100)
    score = (
        (da_norm * 3.0) +   # 30% weight — Domain Authority
        (pa_norm * 2.0) +   # 20% weight — Page Authority
        (tf_norm * 2.0) +   # 20% weight — Trust Flow
        (bl_norm * 1.5) +   # 15% weight — Backlinks
        (wb_norm * 1.5) +   # 15% weight — Archive presence
        safe_pen
    )

    return max(0, min(round(score, 1), 100))


def score_domain(domain_name, pagerank_scores=None):
    """
    Full scoring pipeline for a single domain.
    Returns metrics dict ready for save_metrics().
    """
    logger.info(f"Scoring domain: {domain_name}")

    # PageRank / DA
    da = 0
    if pagerank_scores and domain_name in pagerank_scores:
        da = pagerank_scores[domain_name] * 10  # Convert 0-10 to 0-100 range
    elif pagerank_scores is None:
        pr = get_pagerank([domain_name])
        da = pr.get(domain_name, 0) * 10

    # Wayback
    wb = wayback_check(domain_name)

    # Safe Browsing
    safety = safe_browsing_check([domain_name])
    is_safe = safety.get(domain_name, True)

    # PA and TF approximations (estimated from DA and backlinks)
    # In a real production system, you'd use Moz/Majestic APIs for these
    pa = da * 0.85 if da else 0
    tf = da * 0.6 if da else 0

    composite = compute_score(
        domain_authority=da,
        page_authority=pa,
        trust_flow=tf,
        backlinks=wb['snapshots'] * 2,  # Rough estimate from archive
        wayback_snapshots=wb['snapshots'],
        google_safe=is_safe,
    )

    return {
        'domain_authority': round(da, 1),
        'page_authority': round(pa, 1),
        'trust_flow': round(tf, 1),
        'backlinks': wb['snapshots'] * 2,  # Estimated
        'wayback_snapshots': wb['snapshots'],
        'archive_age_days': wb['archive_age_days'],
        'google_safe': is_safe,
        'composite_score': composite,
    }
