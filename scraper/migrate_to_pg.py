"""
Migrate local SQLite data → Railway PostgreSQL.
Copies all domains + metrics from local ghostdomains.db to production.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import sqlite3
import psycopg2
import psycopg2.extras

SQLITE_PATH = os.path.join(os.path.dirname(__file__), '..', 'ghostdomains.db')
PG_URL = os.environ.get('DATABASE_URL', '')

if not PG_URL or not PG_URL.startswith('postgres'):
    print("ERROR: Set DATABASE_URL env var to your Railway PostgreSQL URL")
    sys.exit(1)

print(f"Connecting to PostgreSQL...")
pg = psycopg2.connect(PG_URL)
pg.autocommit = False
pgc = pg.cursor()

print(f"Reading from SQLite: {SQLITE_PATH}")
sq = sqlite3.connect(SQLITE_PATH)
sq.row_factory = sqlite3.Row

# ─── Init schema ───
print("Initializing PostgreSQL schema...")
schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'init_db_pg.sql')
with open(schema_path) as f:
    schema = f.read()
for stmt in [s.strip() for s in schema.split(';') if s.strip()]:
    pgc.execute(stmt)
pg.commit()
print("Schema ready [OK]")

# ─── Migrate channels ───
channels = sq.execute("SELECT * FROM channels").fetchall()
print(f"Migrating {len(channels)} channels...")
for c in channels:
    pgc.execute("""
        INSERT INTO channels (channel_id, name, subscriber_count, created_date, description, last_scraped_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (channel_id) DO NOTHING
    """, (c['channel_id'], c['name'], c['subscriber_count'],
          c['created_date'], c['description'], c['last_scraped_at']))
pg.commit()

# ─── Migrate domains ───
domains = sq.execute("SELECT * FROM domains WHERE is_expired = 1").fetchall()
print(f"Migrating {len(domains)} expired domains...")
id_map = {}  # old sqlite id → new pg id

for d in domains:
    pgc.execute("""
        INSERT INTO domains (domain, tld, expiry_date, registrar, whois_status,
            dns_resolves, http_status, is_expired, discovery_source,
            source_channel_id, first_found_at, last_checked_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (domain) DO UPDATE SET
            is_expired = EXCLUDED.is_expired,
            last_checked_at = EXCLUDED.last_checked_at
        RETURNING id
    """, (d['domain'], d['tld'], d['expiry_date'], d['registrar'],
          d['whois_status'], bool(d['dns_resolves']), d['http_status'],
          bool(d['is_expired']), d['discovery_source'], d['source_channel_id'],
          d['first_found_at'], d['last_checked_at']))
    row = pgc.fetchone()
    if row:
        id_map[d['id']] = row[0]

pg.commit()
print(f"Domains migrated ✅  ({len(id_map)} inserted/updated)")

# ─── Migrate metrics ───
metrics = sq.execute("SELECT * FROM domain_metrics").fetchall()
print(f"Migrating {len(metrics)} metric records...")
migrated_m = 0
for m in metrics:
    old_id = m['domain_id']
    new_id = id_map.get(old_id)
    if not new_id:
        continue
    pgc.execute("""
        INSERT INTO domain_metrics (domain_id, domain_authority, page_authority,
            trust_flow, backlinks, wayback_snapshots, archive_age_days,
            google_safe, composite_score, scored_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (domain_id) DO UPDATE SET
            domain_authority = EXCLUDED.domain_authority,
            composite_score = EXCLUDED.composite_score,
            scored_at = EXCLUDED.scored_at
    """, (new_id, m['domain_authority'], m['page_authority'],
          m['trust_flow'], m['backlinks'], m['wayback_snapshots'],
          m['archive_age_days'], bool(m['google_safe']),
          m['composite_score'], m['scored_at']))
    migrated_m += 1
pg.commit()
print(f"Metrics migrated ✅  ({migrated_m} records)")

# ─── Verify ───
pgc.execute("SELECT COUNT(*) FROM domains WHERE is_expired = true")
total = pgc.fetchone()[0]
pgc.execute("SELECT COUNT(*) FROM domain_metrics")
mcount = pgc.fetchone()[0]
print(f"\n✅ Migration complete!")
print(f"   Expired domains in PostgreSQL: {total}")
print(f"   Metric records in PostgreSQL:  {mcount}")

pg.close()
sq.close()
