-- GhostDomains Database Schema
-- Compatible with both SQLite (local dev) and PostgreSQL (Railway)

CREATE TABLE IF NOT EXISTS channels (
    channel_id VARCHAR(24) PRIMARY KEY,
    name VARCHAR(255),
    subscriber_count INTEGER DEFAULT 0,
    created_date DATE,
    description TEXT,
    last_scraped_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain VARCHAR(253) UNIQUE NOT NULL,
    tld VARCHAR(63),
    expiry_date DATE,
    registrar VARCHAR(255),
    whois_status VARCHAR(50),
    dns_resolves BOOLEAN,
    http_status INTEGER,
    is_expired BOOLEAN DEFAULT FALSE,
    discovery_source VARCHAR(50) DEFAULT 'manual',
    source_channel_id VARCHAR(24) REFERENCES channels(channel_id),
    first_found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS domain_metrics (
    domain_id INTEGER PRIMARY KEY REFERENCES domains(id),
    domain_authority REAL DEFAULT 0,
    page_authority REAL DEFAULT 0,
    trust_flow REAL DEFAULT 0,
    backlinks INTEGER DEFAULT 0,
    wayback_snapshots INTEGER DEFAULT 0,
    archive_age_days INTEGER DEFAULT 0,
    google_safe BOOLEAN DEFAULT TRUE,
    composite_score REAL DEFAULT 0,
    scored_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saved_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saved_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER REFERENCES saved_lists(id) ON DELETE CASCADE,
    domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS watchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    min_da_threshold INTEGER DEFAULT 20,
    tld_filter VARCHAR(255),
    notify_expiry_days INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id INTEGER REFERENCES domains(id),
    watcher_id INTEGER REFERENCES watchers(id),
    alert_type VARCHAR(20) NOT NULL,
    email_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_domains_expiry ON domains(expiry_date);
CREATE INDEX IF NOT EXISTS idx_domains_tld ON domains(tld);
CREATE INDEX IF NOT EXISTS idx_domains_expired ON domains(is_expired);
CREATE INDEX IF NOT EXISTS idx_domains_found ON domains(first_found_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_composite ON domain_metrics(composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_da ON domain_metrics(domain_authority DESC);
CREATE INDEX IF NOT EXISTS idx_saved_list ON saved_domains(list_id);
