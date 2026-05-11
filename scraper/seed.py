"""Seed the database with sample data for development."""
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scraper.db import init_db, save_domain, save_metrics, save_channel

# Sample channels
channels = [
    {'channel_id': 'UC001', 'name': 'TechReviews2019', 'subscriber_count': 45000, 'created_date': '2018-03-15', 'description': 'Tech reviews at tech-reviews.co.uk'},
    {'channel_id': 'UC002', 'name': 'HealthyEats', 'subscriber_count': 120000, 'created_date': '2017-07-22', 'description': 'Organic recipes at organicrecipes.net'},
    {'channel_id': 'UC003', 'name': 'FitLifeTV', 'subscriber_count': 890000, 'created_date': '2016-01-10', 'description': 'Visit fitnessguru.com for plans'},
    {'channel_id': 'UC004', 'name': 'GamersUnited', 'subscriber_count': 340000, 'created_date': '2019-05-01', 'description': 'Reviews at gamingreviews.gg'},
    {'channel_id': 'UC005', 'name': 'PhotoMaster', 'subscriber_count': 67000, 'created_date': '2017-11-30', 'description': 'Portfolio at photographyhub.org'},
]

# Sample domains with realistic data
domains_data = [
    {'domain': 'tech-reviews.co.uk', 'tld': '.co.uk', 'expiry_date': '2026-06-17', 'registrar': 'Namecheap Inc.', 'whois_status': 'pendingDelete', 'source': 'youtube', 'channel': 'UC001',
     'da': 65, 'pa': 45, 'tf': 30, 'bl': 1240, 'wb': 892, 'age': 18},
    {'domain': 'organicrecipes.net', 'tld': '.net', 'expiry_date': '2026-06-20', 'registrar': 'GoDaddy LLC', 'whois_status': 'pendingDelete', 'source': 'youtube', 'channel': 'UC002',
     'da': 50, 'pa': 46, 'tf': 28, 'bl': 856, 'wb': 1203, 'age': 33},
    {'domain': 'creativeportfolio.io', 'tld': '.io', 'expiry_date': '2026-05-28', 'registrar': 'Dynadot LLC', 'whois_status': 'redemptionPeriod', 'source': 'zone_file', 'channel': None,
     'da': 42, 'pa': 50, 'tf': 34, 'bl': 340, 'wb': 445, 'age': 2},
    {'domain': 'traveltips.blog', 'tld': '.blog', 'expiry_date': '2026-06-05', 'registrar': 'Namecheap Inc.', 'whois_status': 'pendingDelete', 'source': 'ct_log', 'channel': None,
     'da': 35, 'pa': 55, 'tf': 36, 'bl': 2100, 'wb': 678, 'age': 21},
    {'domain': 'traveltips.net', 'tld': '.net', 'expiry_date': '2026-06-12', 'registrar': 'NameSilo LLC', 'whois_status': 'pendingDelete', 'source': 'feed', 'channel': None,
     'da': 30, 'pa': 40, 'tf': 38, 'bl': 980, 'wb': 320, 'age': 21},
    {'domain': 'fitnessguru.com', 'tld': '.com', 'expiry_date': '2026-05-30', 'registrar': 'GoDaddy LLC', 'whois_status': 'pendingDelete', 'source': 'youtube', 'channel': 'UC003',
     'da': 72, 'pa': 61, 'tf': 45, 'bl': 5420, 'wb': 2100, 'age': 45},
    {'domain': 'codingacademy.dev', 'tld': '.dev', 'expiry_date': '2026-06-25', 'registrar': 'Google Domains', 'whois_status': 'pendingDelete', 'source': 'zone_file', 'channel': None,
     'da': 58, 'pa': 52, 'tf': 41, 'bl': 3200, 'wb': 560, 'age': 12},
    {'domain': 'photographyhub.org', 'tld': '.org', 'expiry_date': '2026-07-01', 'registrar': 'Tucows Inc.', 'whois_status': 'pendingDelete', 'source': 'youtube', 'channel': 'UC005',
     'da': 44, 'pa': 38, 'tf': 22, 'bl': 780, 'wb': 390, 'age': 28},
    {'domain': 'musicstreamer.app', 'tld': '.app', 'expiry_date': '2026-05-22', 'registrar': 'Namecheap Inc.', 'whois_status': 'redemptionPeriod', 'source': 'ct_log', 'channel': None,
     'da': 28, 'pa': 32, 'tf': 18, 'bl': 290, 'wb': 150, 'age': 7},
    {'domain': 'gamingreviews.gg', 'tld': '.gg', 'expiry_date': '2026-06-08', 'registrar': 'GoDaddy LLC', 'whois_status': 'pendingDelete', 'source': 'youtube', 'channel': 'UC004',
     'da': 61, 'pa': 55, 'tf': 39, 'bl': 4100, 'wb': 1800, 'age': 35},
    {'domain': 'startuptools.co', 'tld': '.co', 'expiry_date': '2026-06-18', 'registrar': 'Namecheap Inc.', 'whois_status': 'pendingDelete', 'source': 'feed', 'channel': None,
     'da': 55, 'pa': 48, 'tf': 33, 'bl': 2800, 'wb': 720, 'age': 24},
    {'domain': 'designhub.studio', 'tld': '.studio', 'expiry_date': '2026-05-25', 'registrar': 'Dynadot LLC', 'whois_status': 'redemptionPeriod', 'source': 'zone_file', 'channel': None,
     'da': 38, 'pa': 42, 'tf': 25, 'bl': 560, 'wb': 310, 'age': 15},
    {'domain': 'cryptonews.xyz', 'tld': '.xyz', 'expiry_date': '2026-06-02', 'registrar': 'NameSilo LLC', 'whois_status': 'pendingDelete', 'source': 'ct_log', 'channel': None,
     'da': 48, 'pa': 44, 'tf': 20, 'bl': 1900, 'wb': 890, 'age': 30},
    {'domain': 'recipecollection.com', 'tld': '.com', 'expiry_date': '2026-06-22', 'registrar': 'GoDaddy LLC', 'whois_status': 'pendingDelete', 'source': 'youtube', 'channel': 'UC002',
     'da': 40, 'pa': 36, 'tf': 29, 'bl': 1100, 'wb': 550, 'age': 40},
    {'domain': 'learnpython.io', 'tld': '.io', 'expiry_date': '2026-07-05', 'registrar': 'Namecheap Inc.', 'whois_status': 'pendingDelete', 'source': 'feed', 'channel': None,
     'da': 67, 'pa': 58, 'tf': 44, 'bl': 4500, 'wb': 1600, 'age': 50},
]


def seed():
    """Populate database with sample data."""
    from scraper.metrics import compute_score
    init_db()
    print("Seeding database...")

    for ch in channels:
        save_channel(ch)
        print(f"  Channel: {ch['name']}")

    now = datetime.utcnow()
    for i, dd in enumerate(domains_data):
        # Spread first_found_at across last few days for chart data
        days_ago = random.randint(0, 2)
        found_date = (now - timedelta(days=days_ago)).isoformat()

        domain_id = save_domain({
            'domain': dd['domain'],
            'tld': dd['tld'],
            'expiry_date': dd['expiry_date'],
            'registrar': dd['registrar'],
            'whois_status': dd['whois_status'],
            'dns_resolves': False,
            'http_status': None,
            'is_expired': True,
            'discovery_source': dd['source'],
            'source_channel_id': dd['channel'],
        })

        if domain_id:
            score = compute_score(dd['da'], dd['pa'], dd['tf'], dd['bl'], dd['wb'], True)
            save_metrics(domain_id, {
                'domain_authority': dd['da'],
                'page_authority': dd['pa'],
                'trust_flow': dd['tf'],
                'backlinks': dd['bl'],
                'wayback_snapshots': dd['wb'],
                'archive_age_days': dd['age'],
                'google_safe': True,
                'composite_score': score,
            })
            print(f"  Domain: {dd['domain']} (score: {score})")

    print(f"\nSeeded {len(channels)} channels and {len(domains_data)} domains.")
    print("Database ready!")


if __name__ == '__main__':
    seed()
