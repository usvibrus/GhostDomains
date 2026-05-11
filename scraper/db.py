"""
GhostDomains Database Module
Supports both SQLite (local dev) and PostgreSQL (production/Railway).
Detects engine from DATABASE_URL environment variable.
"""
import os
import re
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', '')
USE_PG = DATABASE_URL.startswith('postgres')

if USE_PG:
    import psycopg2
    import psycopg2.extras
else:
    import sqlite3

DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'ghostdomains.db'))
SQL_DIR = os.path.join(os.path.dirname(__file__), '..', 'sql')


def _ph(sql):
    """Convert SQLite ? placeholders to PostgreSQL %s."""
    if USE_PG:
        return sql.replace('?', '%s')
    return sql


@contextmanager
def get_connection():
    """Context manager for database connections (SQLite or PostgreSQL)."""
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        try:
            yield PgConnection(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield SqliteConnection(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class SqliteConnection:
    """Wrapper for SQLite that provides consistent interface."""
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        if params:
            return self._conn.execute(sql, params)
        return self._conn.execute(sql)

    def executescript(self, sql):
        return self._conn.executescript(sql)

    def fetchone(self, sql, params=None):
        cur = self.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def fetchall(self, sql, params=None):
        cur = self.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    def last_insert_id(self):
        return self.execute("SELECT last_insert_rowid() as id").fetchone()[0]


class PgConnection:
    """Wrapper for PostgreSQL that provides consistent interface."""
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        sql = _ph(sql)
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur

    def executescript(self, sql):
        cur = self._conn.cursor()
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        for stmt in statements:
            cur.execute(stmt)
        return cur

    def fetchone(self, sql, params=None):
        cur = self.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

    def fetchall(self, sql, params=None):
        cur = self.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    def last_insert_id(self):
        # Must be called right after an INSERT ... RETURNING id
        return None  # Use RETURNING instead


def init_db():
    """Initialize database from SQL schema file."""
    if USE_PG:
        schema_path = os.path.join(SQL_DIR, 'init_db_pg.sql')
        if not os.path.exists(schema_path):
            schema_path = os.path.join(SQL_DIR, 'init_db.sql')
    else:
        schema_path = os.path.join(SQL_DIR, 'init_db.sql')

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    with get_connection() as conn:
        conn.executescript(schema_sql)
    logger.info(f"Database initialized (engine={'PostgreSQL' if USE_PG else 'SQLite'})")


# ─── Channel Operations ───

def save_channel(channel_data):
    """Upsert a YouTube channel."""
    sql = _ph("""
        INSERT INTO channels (channel_id, name, subscriber_count, created_date, description, last_scraped_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(channel_id) DO UPDATE SET
            name = EXCLUDED.name,
            subscriber_count = EXCLUDED.subscriber_count,
            description = EXCLUDED.description,
            last_scraped_at = EXCLUDED.last_scraped_at
    """)
    with get_connection() as conn:
        conn.execute(sql, (
            channel_data['channel_id'],
            channel_data.get('name', ''),
            channel_data.get('subscriber_count', 0),
            channel_data.get('created_date'),
            channel_data.get('description', ''),
            datetime.utcnow().isoformat(),
        ))


def get_channels_to_scrape(days=7):
    """Get channels that haven't been scraped in `days` days."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    sql = _ph("SELECT * FROM channels WHERE last_scraped_at IS NULL OR last_scraped_at < ?")
    with get_connection() as conn:
        return conn.fetchall(sql, (cutoff,))


def channel_exists(channel_id):
    """Check if a channel already exists in the database."""
    sql = _ph("SELECT 1 FROM channels WHERE channel_id = ?")
    with get_connection() as conn:
        return conn.fetchone(sql, (channel_id,)) is not None


# ─── Domain Operations ───

def save_domain(domain_data):
    """Upsert a domain record. Returns the domain id."""
    if USE_PG:
        sql = """
            INSERT INTO domains (domain, tld, expiry_date, registrar, whois_status,
                dns_resolves, http_status, is_expired, discovery_source,
                source_channel_id, last_checked_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(domain) DO UPDATE SET
                expiry_date = COALESCE(EXCLUDED.expiry_date, domains.expiry_date),
                registrar = COALESCE(EXCLUDED.registrar, domains.registrar),
                whois_status = COALESCE(EXCLUDED.whois_status, domains.whois_status),
                dns_resolves = EXCLUDED.dns_resolves,
                http_status = EXCLUDED.http_status,
                is_expired = EXCLUDED.is_expired,
                last_checked_at = EXCLUDED.last_checked_at
            RETURNING id
        """
    else:
        sql = """
            INSERT INTO domains (domain, tld, expiry_date, registrar, whois_status,
                dns_resolves, http_status, is_expired, discovery_source,
                source_channel_id, last_checked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                expiry_date = COALESCE(excluded.expiry_date, domains.expiry_date),
                registrar = COALESCE(excluded.registrar, domains.registrar),
                whois_status = COALESCE(excluded.whois_status, domains.whois_status),
                dns_resolves = excluded.dns_resolves,
                http_status = excluded.http_status,
                is_expired = excluded.is_expired,
                last_checked_at = excluded.last_checked_at
        """

    params = (
        domain_data['domain'],
        domain_data.get('tld', ''),
        domain_data.get('expiry_date'),
        domain_data.get('registrar'),
        domain_data.get('whois_status'),
        domain_data.get('dns_resolves'),
        domain_data.get('http_status'),
        domain_data.get('is_expired', False),
        domain_data.get('discovery_source', 'manual'),
        domain_data.get('source_channel_id'),
        datetime.utcnow().isoformat(),
    )

    with get_connection() as conn:
        cur = conn.execute(sql, params)
        if USE_PG:
            row = cur.fetchone()
            return row['id'] if row else None
        else:
            row = conn.fetchone("SELECT id FROM domains WHERE domain = ?",
                                (domain_data['domain'],))
            return row['id'] if row else None


def save_metrics(domain_id, metrics_data):
    """Upsert domain metrics."""
    sql = _ph("""
        INSERT INTO domain_metrics (domain_id, domain_authority, page_authority,
            trust_flow, backlinks, wayback_snapshots, archive_age_days,
            google_safe, composite_score, scored_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(domain_id) DO UPDATE SET
            domain_authority = EXCLUDED.domain_authority,
            page_authority = EXCLUDED.page_authority,
            trust_flow = EXCLUDED.trust_flow,
            backlinks = EXCLUDED.backlinks,
            wayback_snapshots = EXCLUDED.wayback_snapshots,
            archive_age_days = EXCLUDED.archive_age_days,
            google_safe = EXCLUDED.google_safe,
            composite_score = EXCLUDED.composite_score,
            scored_at = EXCLUDED.scored_at
    """)
    with get_connection() as conn:
        conn.execute(sql, (
            domain_id,
            metrics_data.get('domain_authority', 0),
            metrics_data.get('page_authority', 0),
            metrics_data.get('trust_flow', 0),
            metrics_data.get('backlinks', 0),
            metrics_data.get('wayback_snapshots', 0),
            metrics_data.get('archive_age_days', 0),
            metrics_data.get('google_safe', True),
            metrics_data.get('composite_score', 0),
            datetime.utcnow().isoformat(),
        ))


def get_domains(page=1, per_page=20, sort='composite_score', order='desc',
                min_da=None, min_pa=None, tld=None, source=None,
                is_expired=None, search=None, expiry_within=None):
    """Get paginated, filtered domain list with metrics."""
    conditions = []
    params = []

    if min_da is not None:
        conditions.append("dm.domain_authority >= ?")
        params.append(min_da)
    if min_pa is not None:
        conditions.append("dm.page_authority >= ?")
        params.append(min_pa)
    if tld:
        conditions.append("d.tld = ?")
        params.append(tld)
    if source:
        conditions.append("d.discovery_source = ?")
        params.append(source)
    if is_expired is not None:
        conditions.append("d.is_expired = ?")
        params.append(True if is_expired else False)
    if search:
        conditions.append("d.domain LIKE ?")
        params.append(f"%{search}%")
    if expiry_within:
        cutoff = (datetime.utcnow() + timedelta(days=expiry_within)).isoformat()
        conditions.append("d.expiry_date <= ?")
        params.append(cutoff)

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Map sort field to column
    sort_map = {
        'composite_score': 'dm.composite_score',
        'da': 'dm.domain_authority',
        'pa': 'dm.page_authority',
        'tf': 'dm.trust_flow',
        'backlinks': 'dm.backlinks',
        'expiry': 'd.expiry_date',
        'domain': 'd.domain',
        'archive': 'dm.archive_age_days',
        'found': 'd.first_found_at',
    }
    sort_col = sort_map.get(sort, 'dm.composite_score')
    order_dir = 'DESC' if order == 'desc' else 'ASC'

    offset = (page - 1) * per_page

    count_sql = _ph(f"""
        SELECT COUNT(*) as total FROM domains d
        LEFT JOIN domain_metrics dm ON d.id = dm.domain_id
        {where_clause}
    """)

    query_sql = _ph(f"""
        SELECT d.*, dm.domain_authority, dm.page_authority, dm.trust_flow,
               dm.backlinks, dm.wayback_snapshots, dm.archive_age_days,
               dm.google_safe, dm.composite_score, dm.scored_at
        FROM domains d
        LEFT JOIN domain_metrics dm ON d.id = dm.domain_id
        {where_clause}
        ORDER BY {sort_col} {order_dir} NULLS LAST
        LIMIT ? OFFSET ?
    """)

    with get_connection() as conn:
        total_row = conn.fetchone(count_sql, params)
        total = total_row['total'] if total_row else 0
        rows = conn.fetchall(query_sql, params + [per_page, offset])

    return {
        'data': [_domain_row_to_dict(r) for r in rows],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
    }


def get_domain_by_id(domain_id):
    """Get full domain details by ID."""
    sql = _ph("""
        SELECT d.*, dm.domain_authority, dm.page_authority, dm.trust_flow,
               dm.backlinks, dm.wayback_snapshots, dm.archive_age_days,
               dm.google_safe, dm.composite_score, dm.scored_at,
               c.name as channel_name
        FROM domains d
        LEFT JOIN domain_metrics dm ON d.id = dm.domain_id
        LEFT JOIN channels c ON d.source_channel_id = c.channel_id
        WHERE d.id = ?
    """)
    with get_connection() as conn:
        row = conn.fetchone(sql, (domain_id,))
    return _domain_row_to_dict(row) if row else None


def get_stats():
    """Get dashboard statistics."""
    today = datetime.utcnow().date().isoformat()
    yesterday = (datetime.utcnow().date() - timedelta(days=1)).isoformat()

    with get_connection() as conn:
        r1 = conn.fetchone("SELECT COUNT(*) as c FROM domains WHERE is_expired = true")
        total = r1['c'] if r1 else 0

        r2 = conn.fetchone(_ph("SELECT COUNT(*) as c FROM domains WHERE date(first_found_at) = ?"), (today,))
        today_count = r2['c'] if r2 else 0

        r3 = conn.fetchone(_ph("SELECT COUNT(*) as c FROM domains WHERE date(first_found_at) = ?"), (yesterday,))
        yesterday_count = r3['c'] if r3 else 0

        change = 0
        if yesterday_count > 0:
            change = round(((today_count - yesterday_count) / yesterday_count) * 100, 1)

        week_cutoff = (datetime.utcnow() + timedelta(days=7)).isoformat()
        r4 = conn.fetchone(
            _ph("SELECT COUNT(*) as c FROM domains WHERE expiry_date <= ? AND is_expired = false"),
            (week_cutoff,)
        )
        expiring_week = r4['c'] if r4 else 0

        r5 = conn.fetchone("SELECT COUNT(*) as c FROM domain_metrics WHERE composite_score >= 70")
        high_score = r5['c'] if r5 else 0

        sources = conn.fetchall("""
            SELECT discovery_source, COUNT(*) as count FROM domains
            GROUP BY discovery_source ORDER BY count DESC
        """)

    return {
        'found_today': today_count,
        'found_today_change': change,
        'total_found': total,
        'expiring_this_week': expiring_week,
        'high_score_count': high_score,
        'growth_label': 'Growth: Last 30 Days',
        'source_breakdown': {r['discovery_source']: r['count'] for r in sources},
    }


def get_chart_data(days=30):
    """Get daily domain counts for sparkline chart."""
    start = (datetime.utcnow() - timedelta(days=days)).isoformat()
    sql = _ph("""
        SELECT date(first_found_at) as day, COUNT(*) as count
        FROM domains
        WHERE first_found_at >= ?
        GROUP BY date(first_found_at)
        ORDER BY day ASC
    """)
    with get_connection() as conn:
        rows = conn.fetchall(sql, (start,))
    return [{'day': str(r['day']), 'count': r['count']} for r in rows]


def get_domains_to_recheck(hours=24):
    """Get domains that need WHOIS/DNS rechecking."""
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    sql = _ph("""
        SELECT * FROM domains
        WHERE last_checked_at IS NULL OR last_checked_at < ?
        ORDER BY last_checked_at ASC
        LIMIT 500
    """)
    with get_connection() as conn:
        return conn.fetchall(sql, (cutoff,))


def get_expiring_domains(days=30, min_score=0):
    """Get domains expiring within N days, above min score."""
    cutoff = (datetime.utcnow() + timedelta(days=days)).isoformat()
    sql = _ph("""
        SELECT d.*, dm.composite_score
        FROM domains d
        LEFT JOIN domain_metrics dm ON d.id = dm.domain_id
        WHERE d.expiry_date <= ?
          AND d.is_expired = false
          AND (dm.composite_score >= ? OR dm.composite_score IS NULL)
        ORDER BY dm.composite_score DESC
    """)
    with get_connection() as conn:
        return conn.fetchall(sql, (cutoff, min_score))


# ─── Saved Lists ───

def create_saved_list(name):
    if USE_PG:
        sql = "INSERT INTO saved_lists (name) VALUES (%s) RETURNING id"
        with get_connection() as conn:
            cur = conn.execute(sql, (name,))
            return cur.fetchone()['id']
    else:
        with get_connection() as conn:
            conn.execute("INSERT INTO saved_lists (name) VALUES (?)", (name,))
            return conn.last_insert_id()


def get_saved_lists():
    with get_connection() as conn:
        return conn.fetchall("""
            SELECT sl.*, COUNT(sd.id) as domain_count
            FROM saved_lists sl
            LEFT JOIN saved_domains sd ON sl.id = sd.list_id
            GROUP BY sl.id ORDER BY sl.created_at DESC
        """)


def add_domain_to_list(list_id, domain_id, notes=''):
    sql = _ph("""
        INSERT INTO saved_domains (list_id, domain_id, notes)
        VALUES (?, ?, ?)
        ON CONFLICT DO NOTHING
    """)
    with get_connection() as conn:
        conn.execute(sql, (list_id, domain_id, notes))


def get_saved_list_domains(list_id):
    sql = _ph("""
        SELECT d.*, dm.domain_authority, dm.page_authority, dm.trust_flow,
               dm.backlinks, dm.composite_score, sd.notes, sd.added_at
        FROM saved_domains sd
        JOIN domains d ON sd.domain_id = d.id
        LEFT JOIN domain_metrics dm ON d.id = dm.domain_id
        WHERE sd.list_id = ?
        ORDER BY sd.added_at DESC
    """)
    with get_connection() as conn:
        return [_domain_row_to_dict(r) for r in conn.fetchall(sql, (list_id,))]


# ─── Watchers ───

def create_watcher(email, min_da=20, tld_filter=None, notify_days=30):
    if USE_PG:
        sql = """INSERT INTO watchers (email, min_da_threshold, tld_filter, notify_expiry_days)
                 VALUES (%s, %s, %s, %s) RETURNING id"""
        with get_connection() as conn:
            cur = conn.execute(sql, (email, min_da, tld_filter, notify_days))
            return cur.fetchone()['id']
    else:
        sql = _ph("""INSERT INTO watchers (email, min_da_threshold, tld_filter, notify_expiry_days)
                     VALUES (?, ?, ?, ?)""")
        with get_connection() as conn:
            conn.execute(sql, (email, min_da, tld_filter, notify_days))
            return conn.last_insert_id()


def get_watchers():
    with get_connection() as conn:
        return conn.fetchall("SELECT * FROM watchers ORDER BY created_at DESC")


def delete_watcher(watcher_id):
    sql = _ph("DELETE FROM watchers WHERE id = ?")
    with get_connection() as conn:
        conn.execute(sql, (watcher_id,))


# ─── Alerts ───

def get_unsent_alerts_for_watcher(watcher_id):
    sql = _ph("""
        SELECT a.*, d.domain, dm.composite_score
        FROM alerts a
        JOIN domains d ON a.domain_id = d.id
        LEFT JOIN domain_metrics dm ON d.id = dm.domain_id
        WHERE a.watcher_id = ? AND a.email_sent = false
    """)
    with get_connection() as conn:
        return conn.fetchall(sql, (watcher_id,))


def mark_alert_sent(alert_id):
    sql = _ph("UPDATE alerts SET email_sent = true, sent_at = ? WHERE id = ?")
    with get_connection() as conn:
        conn.execute(sql, (datetime.utcnow().isoformat(), alert_id))


def create_alert(domain_id, watcher_id, alert_type):
    """Create alert if one doesn't already exist for this domain+watcher."""
    check_sql = _ph("""
        SELECT 1 FROM alerts WHERE domain_id = ? AND watcher_id = ? AND alert_type = ?
    """)
    insert_sql = _ph("""
        INSERT INTO alerts (domain_id, watcher_id, alert_type)
        VALUES (?, ?, ?)
    """)
    with get_connection() as conn:
        existing = conn.fetchone(check_sql, (domain_id, watcher_id, alert_type))
        if not existing:
            conn.execute(insert_sql, (domain_id, watcher_id, alert_type))


# ─── Helpers ───

def _domain_row_to_dict(row):
    """Convert a database row to a clean dictionary."""
    if row is None:
        return None
    d = dict(row)
    # Nest metrics under 'metrics' key for API compatibility
    metrics_keys = ['domain_authority', 'page_authority', 'trust_flow',
                    'backlinks', 'wayback_snapshots', 'archive_age_days',
                    'google_safe', 'composite_score', 'scored_at']
    metrics = {}
    for key in metrics_keys:
        if key in d:
            metrics[key] = d.pop(key)
    if metrics:
        d['metrics'] = metrics
    return d


def domain_exists(domain_name):
    """Check if a domain exists in the database."""
    sql = _ph("SELECT id FROM domains WHERE domain = ?")
    with get_connection() as conn:
        return conn.fetchone(sql, (domain_name,))
