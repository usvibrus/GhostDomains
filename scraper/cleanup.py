"""Clean junk/false-positive domains from the database."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scraper.extractor import has_valid_tld, is_skip_domain
from scraper.db import get_connection, _ph

def clean():
    with get_connection() as conn:
        rows = conn.fetchall("SELECT id, domain FROM domains")
        to_delete = []
        for r in rows:
            domain = r['domain']
            # Remove if invalid TLD or should be skipped
            if not has_valid_tld(domain) or is_skip_domain(domain):
                to_delete.append((r['id'], domain))

        if not to_delete:
            print("No junk domains found!")
            return

        print(f"Removing {len(to_delete)} junk domains:")
        for did, name in to_delete:
            print(f"  - {name}")
            conn.execute(_ph("DELETE FROM domain_metrics WHERE domain_id = ?"), (did,))
            conn.execute(_ph("DELETE FROM domains WHERE id = ?"), (did,))

        remaining = conn.fetchone("SELECT COUNT(*) as c FROM domains")
        expired = conn.fetchone("SELECT COUNT(*) as c FROM domains WHERE is_expired = true")
        print(f"\nDone! Remaining: {remaining['c']} total, {expired['c']} expired")

if __name__ == '__main__':
    clean()
