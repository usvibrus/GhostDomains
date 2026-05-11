import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Centralized configuration from environment variables."""

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///ghostdomains.db')
    DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'ghostdomains.db'))

    # YouTube API
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
    YOUTUBE_CHANNELS_BEFORE = os.getenv('YOUTUBE_CHANNELS_BEFORE', '2022-01-01T00:00:00Z')
    YOUTUBE_DAILY_QUOTA = 10000
    YOUTUBE_SEARCH_COST = 100  # units per search.list call
    YOUTUBE_CHANNEL_COST = 1   # units per channels.list call

    # APIs
    GOOGLE_SAFE_BROWSING_KEY = os.getenv('GOOGLE_SAFE_BROWSING_KEY', '')
    OPEN_PAGERANK_KEY = os.getenv('OPEN_PAGERANK_KEY', '')

    # API Security
    API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'dev-secret-key')

    # Email (Resend)
    RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
    ALERT_FROM_EMAIL = os.getenv('ALERT_FROM_EMAIL', 'alerts@ghostdomains.app')

    # Rate limiting
    WHOIS_DELAY = 1.0      # seconds between WHOIS lookups
    HTTP_DELAY = 1.0       # seconds between HTTP checks
    WAYBACK_DELAY = 0.5    # seconds between Wayback API calls
    HTTP_TIMEOUT = 5       # seconds

    # Scraper settings
    RECHECK_INTERVAL_HOURS = 24
    CHANNEL_RESCRAPE_DAYS = 7

    @classmethod
    def validate(cls):
        """Fail fast if critical env vars are missing."""
        missing = []
        if not cls.DATABASE_URL and not cls.DB_PATH:
            missing.append('DATABASE_URL or DB_PATH')
        if missing:
            raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")
        return True

    @classmethod
    def has_youtube(cls):
        return bool(cls.YOUTUBE_API_KEY)

    @classmethod
    def has_safe_browsing(cls):
        return bool(cls.GOOGLE_SAFE_BROWSING_KEY)

    @classmethod
    def has_resend(cls):
        return bool(cls.RESEND_API_KEY)
