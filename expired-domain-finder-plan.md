# GhostDomains — Expired Domain Finder Implementation Plan

> A universal expired domain discovery platform with a premium dark-themed dashboard.
> Stack: Python · Flask · React (Vite) · Railway

---

## Vision

A **hybrid expired domain discovery platform** with two core pipelines:
1. **YouTube Scraping (~50%)** — Scrape channel descriptions from channels created before 2022 to find dead/expired links
2. **External Sources (~50%)** — Zone file diffs, expired domain feeds, CT logs, manual lookup

Both pipelines feed into the same database and dashboard. The UI is source-agnostic — users see all domains in one unified view. Future versions will add more discovery sources (Reddit, forums, blog rolls, etc.).

---

## Tech Stack

| Layer | Tool | Cost |
|---|---|---|
| YouTube scraping | YouTube Data API v3 (10K units/day) | Free |
| External discovery | Zone file parsing, CT logs, expired domain feeds | Free |
| WHOIS check | `python-whois` + `whoisit` fallback | Free |
| DNS check | `dnspython` | Free |
| SEO metrics | Open PageRank API (DA proxy) | Free |
| Backlink estimate | CommonCrawl Index API | Free |
| History/Archive | Wayback Machine CDX API | Free |
| Safety check | Google Safe Browsing API | Free |
| Database | Railway Postgres | ~$5/mo |
| Backend | Flask (Railway) | Included |
| Frontend | React + Vite (Railway) | Included |
| Cron jobs | Railway cron | Included |
| Email alerts | Resend (3,000/month) | Free |

**Estimated monthly cost: ~$5** (Railway Hobby plan)

---

## UI Design Reference

The dashboard follows the reference UI with these key screens:

### 1. Dashboard Overview (Landing Page)
- **Left sidebar** (dark): Logo, navigation (Dashboard, Domain Search, Filters, Saved Lists, Alerts, Reports, Settings, Help)
- **Top section**: Two stat cards:
  - "Expired Domains Found Today" — big number + % change vs yesterday
  - "Total Expired Domains Found" — big number + sparkline growth chart
- **Bottom section**: "Recent Domain Findings" table with:
  - Search bar + date picker + Min DA dropdown + Min PA dropdown + view toggles (grid/list)
  - Sortable columns: Domain Name, Expiration Date, DA, PA, TF (Trust Flow), Backlinks, Archive Age, Actions
  - Actions: "Add to Saved" + "Export" per row

### 2. Domain Detail Page (click a domain row)
- Full WHOIS information (registrar, dates, status)
- SEO metrics breakdown (DA, PA, Trust Flow, backlinks)
- Wayback Machine history + archive age
- Google Safe Browsing status
- Source of discovery
- Quick-action buttons: Save to list, Export, Buy links (GoDaddy, Namecheap, Dynadot)

### 3. Saved Lists Page
- User's saved/bookmarked domains organized in custom lists
- Bulk export (CSV/JSON)

### 4. Domain Search Page
- Manual domain lookup — enter any domain to check status and metrics

### 5. Alerts Page
- Configure email alerts for domains matching criteria (min DA, specific TLDs, etc.)

---

## Project Folder Structure

```
GhostDomains/
├── scraper/
│   ├── main.py               # Entry point, runs discovery pipeline
│   ├── youtube.py             # YouTube API — channel search + description scraping
│   ├── external.py            # External sources — zone files, feeds, CT logs
│   ├── extractor.py           # URL/domain parsing & cleaning
│   ├── checker.py             # WHOIS, DNS, HTTP checks with retry
│   ├── metrics.py             # DA, PA, Trust Flow, backlinks scoring
│   ├── alerts.py              # Resend email alerts
│   ├── db.py                  # Postgres helpers
│   ├── config.py              # Centralized env config
│   ├── requirements.txt
│   └── Dockerfile
├── api/
│   ├── app.py                 # Flask REST API
│   ├── middleware.py           # Auth, rate limiting
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js             # API client
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── DomainDetail.jsx
│   │   │   ├── DomainSearch.jsx
│   │   │   ├── SavedLists.jsx
│   │   │   └── Alerts.jsx
│   │   └── components/
│   │       ├── Sidebar.jsx
│   │       ├── StatsCards.jsx
│   │       ├── DomainTable.jsx
│   │       ├── FilterBar.jsx
│   │       └── SparklineChart.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── tests/
│   ├── test_extractor.py
│   ├── test_checker.py
│   ├── test_metrics.py
│   └── test_api.py
├── sql/
│   └── init_db.sql
├── .env.example
├── .gitignore
├── railway.toml
└── README.md
```

---

## Database Schema

### `channels` (YouTube source tracking)
| Column | Type | Notes |
|---|---|---|
| channel_id | VARCHAR(24) PK | YouTube channel ID |
| name | VARCHAR(255) | Channel display name |
| subscriber_count | INTEGER | Used in scoring context |
| created_date | DATE | Must be before 2022 |
| description | TEXT | Raw description text |
| last_scraped_at | TIMESTAMP | Skip if recently scraped |

### `domains`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| domain | VARCHAR(253) UNIQUE | Root domain e.g. `example.com` |
| tld | VARCHAR(63) | `.com`, `.net`, `.io`, etc. |
| expiry_date | DATE | From WHOIS |
| registrar | VARCHAR(255) | From WHOIS |
| whois_status | VARCHAR(50) | `active`, `pendingDelete`, `redemptionPeriod` |
| dns_resolves | BOOLEAN | From DNS lookup |
| http_status | INTEGER | From HEAD request |
| is_expired | BOOLEAN | Computed flag |
| discovery_source | VARCHAR(50) | `youtube`, `zone_file`, `ct_log`, `feed`, `manual` |
| source_channel_id | VARCHAR(24) FK NULL | References `channels` (only for YouTube-sourced domains) |
| first_found_at | TIMESTAMP DEFAULT NOW() | When first discovered |
| last_checked_at | TIMESTAMP | For recheck scheduling |

### `domain_metrics`
| Column | Type | Notes |
|---|---|---|
| domain_id | INTEGER PK FK | References `domains.id` |
| domain_authority | FLOAT | DA score 0–100 (from Open PageRank) |
| page_authority | FLOAT | PA score 0–100 |
| trust_flow | FLOAT | TF score 0–100 |
| backlinks | INTEGER | Estimated backlink count |
| wayback_snapshots | INTEGER | Archive.org snapshot count |
| archive_age_days | INTEGER | Days since first Wayback snapshot |
| google_safe | BOOLEAN | Safe Browsing check |
| composite_score | FLOAT | Final ranking 0–100 |
| scored_at | TIMESTAMP | |

### `saved_lists`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| name | VARCHAR(255) | List name |
| created_at | TIMESTAMP | |

### `saved_domains`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| list_id | INTEGER FK | References `saved_lists` |
| domain_id | INTEGER FK | References `domains` |
| added_at | TIMESTAMP | |
| notes | TEXT | User notes |

### `watchers` (alert subscribers)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| email | VARCHAR(255) UNIQUE | |
| min_da_threshold | INTEGER DEFAULT 20 | |
| tld_filter | VARCHAR(255) | Comma-separated TLDs or NULL for all |
| notify_expiry_days | INTEGER DEFAULT 30 | |
| created_at | TIMESTAMP | |

### `alerts`
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| domain_id | INTEGER FK | |
| watcher_id | INTEGER FK | |
| alert_type | VARCHAR(20) | `expiry_soon`, `just_dropped`, `high_value` |
| email_sent | BOOLEAN DEFAULT FALSE | |
| sent_at | TIMESTAMP | |

### Indexes
```sql
CREATE INDEX idx_domains_expiry ON domains(expiry_date);
CREATE INDEX idx_domains_tld ON domains(tld);
CREATE INDEX idx_domains_expired ON domains(is_expired);
CREATE INDEX idx_domains_found ON domains(first_found_at DESC);
CREATE INDEX idx_metrics_composite ON domain_metrics(composite_score DESC);
CREATE INDEX idx_metrics_da ON domain_metrics(domain_authority DESC);
CREATE INDEX idx_saved_list ON saved_domains(list_id);
```

---

## Milestones

### Milestone 1 — Setup (Day 1–2)
- [ ] Railway project + Postgres DB + env vars
- [ ] GitHub repo with `.gitignore` (`.env`, `__pycache__/`, `node_modules/`)
- [ ] `.env.example` with all required vars
- [ ] Python venv + deps: `python-whois whoisit dnspython requests psycopg2-binary flask flask-cors flask-limiter tenacity`
- [ ] Vite React app: `npm create vite@latest dashboard -- --template react`
- [ ] `config.py` — centralized env loading with fail-fast validation

### Milestone 2 — Database (Day 2–3)
- [ ] `sql/init_db.sql` — all tables, constraints, indexes
- [ ] `db.py` — upsert helpers for domains, metrics, saved lists, watchers
- [ ] Test DB connection locally

### Milestone 3 — Scraper Pipeline (Day 3–8)

**YouTube Pipeline (`youtube.py`):**
- [ ] `search_channels()` — YouTube API `search.list` with `publishedBefore=2022-01-01T00:00:00Z`, `type=channel`
- [ ] `fetch_descriptions(channel_ids)` — `channels.list` batch 50 IDs (1 unit/call, cheap)
- [ ] Save channels to DB; skip if `last_scraped_at` < 7 days
- [ ] Extract all URLs from descriptions → feed into checker pipeline

**External Pipeline (`external.py`):**
- [ ] Expired domain feed parsers (ExpiredDomains.net feeds, zone file diffs)
- [ ] CT log monitoring for expiring certificates
- [ ] Pluggable source interface for adding more sources later

**Shared modules:**
- [ ] `extractor.py` — domain parsing, TLD extraction, redirect resolution, deduplication
- [ ] `checker.py` — WHOIS (with fallback + retry), DNS, HTTP checks
- [ ] `metrics.py` — Open PageRank (DA), backlink estimation, Wayback CDX, Safe Browsing
- [ ] `main.py` — orchestrator with `--mode youtube|external|full|recheck` CLI flags
- [ ] Structured logging throughout

### Milestone 4 — Flask API (Day 8–11)
- [ ] `GET /domains` — paginated, filterable (sort, min_da, min_pa, tld, expiry_within, source, date range)
- [ ] `GET /domains/:id` — full detail with metrics + source channel info if YouTube-sourced
- [ ] `GET /domains/export?format=csv|json` — bulk export with same filters
- [ ] `GET /stats` — today's count, total count, % change, top TLDs, source breakdown
- [ ] `GET /stats/chart` — daily counts for sparkline (last 30 days)
- [ ] CRUD for saved lists + saved domains
- [ ] CRUD for watchers
- [ ] `POST /domains/lookup` — manual domain check
- [ ] API key auth + rate limiting + CORS

### Milestone 5 — React Dashboard (Day 11–16)
- [ ] Dark theme matching reference UI (dark sidebar, dark cards, accent colors)
- [ ] `Sidebar` — navigation with active state highlighting
- [ ] `StatsCards` — "Found Today" with % change + "Total Found" with sparkline chart
- [ ] `DomainTable` — sortable columns (Domain, Expiry, DA, PA, TF, Backlinks, Archive Age, Source, Actions)
- [ ] `FilterBar` — search, date picker, Min DA, Min PA dropdowns, source filter, grid/list view toggle
- [ ] `DomainDetail` page — full info on click (shows YouTube channel link if YouTube-sourced)
- [ ] `SavedLists` page — manage saved domains
- [ ] `Alerts` page — configure email alerts
- [ ] `DomainSearch` page — manual lookup
- [ ] Responsive + mobile-friendly

### Milestone 6 — Testing & Deploy (Day 16–19)
- [ ] Unit tests for extractor, checker, metrics
- [ ] Integration test: both pipelines end-to-end
- [ ] Deploy all services to Railway
- [ ] Verify cron jobs, alerts, dashboard
- [ ] README with setup docs

---

## Cron Schedule

| Job | Command | Schedule |
|---|---|---|
| YouTube scrape | `python main.py --mode youtube` | Daily 02:00 UTC |
| External scrape | `python main.py --mode external` | Daily 03:00 UTC |
| Expiry recheck | `python main.py --mode recheck` | Every 6 hours |
| Alert check | `python alerts.py` | Daily 08:00 UTC |

---

## Error Handling

| Failure | Strategy |
|---|---|
| WHOIS fails | Retry 3× with backoff; fallback to `whoisit` |
| DNS timeout | Retry 2×; mark as unknown |
| YouTube API quota exhausted | Stop YouTube pipeline, log warning, external pipeline continues |
| Other API quota exhausted | Stop run, log warning, continue next cycle |
| Email fails | Log error, retry next cron run |
| DB connection lost | Retry 3× with backoff; crash if unrecoverable |

---

## Env Variables

```env
DATABASE_URL=
YOUTUBE_API_KEY=
RESEND_API_KEY=
GOOGLE_SAFE_BROWSING_KEY=
API_SECRET_KEY=
VITE_API_URL=
```
