# 👻 GhostDomains — Expired Domain Finder

> Discover high-value expired domains with SEO metrics, sourced from YouTube channels and external feeds.

**Live:** [https://ghostedomains.site](https://ghostedomains.site)

---

## Features

- 🔍 **Hybrid Discovery** — Finds expired domains from YouTube channel descriptions (pre-2022) + external sources (CT logs, feeds)
- 📊 **SEO Metrics** — Domain Authority, Page Authority, Trust Flow, Backlinks, Archive Age
- 🎨 **Premium Dashboard** — Dark-themed React UI with real-time stats, sortable tables, and domain detail pages
- 💾 **Save & Export** — Bookmark domains to lists, export as CSV/JSON
- 🔔 **Email Alerts** — Get notified when domains matching your criteria expire
- 🔎 **Manual Lookup** — Check any domain's status on demand

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, Recharts, Lucide Icons |
| Backend | Flask, Gunicorn |
| Database | PostgreSQL (production) / SQLite (dev) |
| Scraper | Python (WHOIS, DNS, YouTube API, Wayback Machine) |
| Hosting | Railway |
| Domain | ghostedomains.site |

## Quick Start (Local Dev)

```bash
# 1. Clone
git clone https://github.com/usvibrus/GhostDomains.git
cd GhostDomains

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 3. Install Python deps
pip install -r requirements.txt

# 4. Install frontend deps & build
cd dashboard && npm install && npm run build && cd ..

# 5. Seed database (optional, for demo data)
python scraper/seed.py

# 6. Run
python api/app.py
# Open http://localhost:5000
```

## Running the Scraper

```bash
python scraper/main.py --mode full       # YouTube + External (~15-20 min)
python scraper/main.py --mode youtube    # YouTube only (~10-15 min)
python scraper/main.py --mode external   # External only (~2-5 min)
python scraper/main.py --mode recheck    # Re-verify existing domains
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Production | PostgreSQL connection string |
| `YOUTUBE_API_KEY` | For scraping | YouTube Data API v3 key |
| `OPEN_PAGERANK_KEY` | For DA scores | Open PageRank API key |
| `API_SECRET_KEY` | Production | API authentication key |
| `RESEND_API_KEY` | For alerts | Resend email API key |
| `GOOGLE_SAFE_BROWSING_KEY` | Optional | Safe Browsing API key |

## Deployment (Railway)

1. Push to GitHub
2. Connect repo to Railway
3. Add PostgreSQL addon
4. Set environment variables
5. Deploy — Railway uses the `Dockerfile` automatically

## License

MIT
