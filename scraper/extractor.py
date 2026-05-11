import re
import logging
from urllib.parse import urlparse
import requests

logger = logging.getLogger(__name__)

# Regex to match URLs in text
URL_PATTERN = re.compile(
    r'https?://[^\s<>"\')\]]+|'           # Full URLs
    r'(?:www\.)[^\s<>"\')\]]+|'           # www. prefixed
    r'[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-z]{2,}(?:/[^\s<>"\')\]]*)?',  # bare domains
    re.IGNORECASE
)

# Valid TLDs — reject anything not in this set to avoid false positives
# like "talk.stay", "channel.the", "videos.if", "home.every"
VALID_TLDS = {
    'com', 'net', 'org', 'io', 'co', 'dev', 'app', 'me', 'info', 'biz',
    'us', 'uk', 'de', 'fr', 'es', 'it', 'nl', 'be', 'at', 'ch', 'ru',
    'jp', 'cn', 'kr', 'au', 'ca', 'br', 'in', 'mx', 'pl', 'se', 'no',
    'fi', 'dk', 'pt', 'cz', 'ie', 'nz', 'za', 'sg', 'hk', 'tw', 'th',
    'id', 'ph', 'my', 'vn', 'ar', 'cl', 'co', 'pe', 'ua', 'ro', 'hu',
    'gr', 'sk', 'bg', 'hr', 'lt', 'lv', 'ee', 'si',
    'xyz', 'site', 'online', 'store', 'tech', 'blog', 'club', 'live',
    'space', 'fun', 'pro', 'top', 'icu', 'vip', 'shop', 'work',
    'world', 'life', 'website', 'cloud', 'design', 'art', 'page',
    'digital', 'media', 'news', 'video', 'game', 'music', 'studio',
    'agency', 'solutions', 'network', 'systems', 'group', 'global',
    'education', 'academy', 'training', 'health', 'fitness',
    'travel', 'food', 'recipes', 'photo', 'photography',
    'tv', 'gg', 'cc', 'ly', 'to', 'fm', 'am', 'la', 'ai', 'vc',
    'ws', 'gl', 'gd', 'is', 'im', 'sh', 'ac', 'ms',
    'mobi', 'tel', 'name', 'aero', 'coop', 'museum', 'jobs', 'travel',
    'gov', 'edu', 'mil', 'int',
}

# Two-part TLDs (e.g., co.uk, com.au)
VALID_TWO_PART_TLDS = {
    'co.uk', 'org.uk', 'me.uk', 'com.au', 'net.au', 'org.au',
    'co.nz', 'co.in', 'co.za', 'co.kr', 'co.jp', 'com.br',
    'com.mx', 'com.ar', 'com.co', 'com.sg', 'com.hk', 'com.tw',
    'com.my', 'com.ph', 'com.vn', 'com.tr', 'com.ua', 'com.eg',
    'com.pk', 'com.ng', 'com.bd', 'co.id', 'co.th',
    'org.in', 'net.in', 'gov.in', 'ac.in',
    'ac.uk', 'gov.uk', 'nhs.uk',
}

# Common non-domain URLs to skip
SKIP_DOMAINS = {
    'youtube.com', 'youtu.be', 'google.com', 'facebook.com',
    'twitter.com', 'x.com', 'instagram.com', 'tiktok.com',
    'linkedin.com', 'reddit.com', 'pinterest.com', 'twitch.tv',
    'discord.gg', 'discord.com', 'bit.ly', 't.co', 'goo.gl',
    'amzn.to', 'amazon.com', 'paypal.com', 'paypal.me',
    'patreon.com', 'ko-fi.com', 'buymeacoffee.com',
    'soundcloud.com', 'spotify.com', 'apple.com',
    'github.com', 'gitlab.com', 'stackoverflow.com',
    # Email providers — never expired
    'gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com',
    'protonmail.com', 'icloud.com', 'mail.com', 'aol.com',
    'zoho.com', 'yandex.com', 'live.com', 'msn.com',
    # Other major platforms
    'wikipedia.org', 'medium.com', 'wordpress.com', 'blogspot.com',
    'tumblr.com', 'snapchat.com', 'whatsapp.com', 'telegram.org',
    'microsoft.com', 'netflix.com', 'ebay.com', 'etsy.com',
    'shopify.com', 'wix.com', 'squarespace.com',
    # Google services
    'googleblog.com', 'blogger.com', 'google.co.in',
    'googleapis.com', 'googleusercontent.com',
    # Other major sites that will never expire
    'fb.com', 'fb.me', 'wa.me', 'deezer.com', 'invideo.io',
    'streamyard.com', 'benchmarkemail.com',
}

# Known URL shorteners that need resolving
SHORTENERS = {'bit.ly', 't.co', 'goo.gl', 'ow.ly', 'tinyurl.com', 'is.gd', 'buff.ly'}


def has_valid_tld(domain):
    """Check if domain has a recognized TLD."""
    if not domain:
        return False
    parts = domain.split('.')
    if len(parts) < 2:
        return False

    # Check two-part TLDs first (e.g., co.uk)
    if len(parts) >= 3:
        two_part = '.'.join(parts[-2:])
        if two_part in VALID_TWO_PART_TLDS:
            return True

    # Check single TLD
    tld = parts[-1].lower()
    return tld in VALID_TLDS


def extract_urls(text):
    """Extract all URLs from a text string."""
    if not text:
        return []
    matches = URL_PATTERN.findall(text)
    urls = []
    for match in matches:
        url = match.strip('.,;:!?')
        if not url.startswith('http'):
            url = 'http://' + url
        urls.append(url)
    return list(set(urls))


def clean_domain(url):
    """Extract root domain from a URL, stripping subpaths and params."""
    try:
        if not url.startswith('http'):
            url = 'http://' + url
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return None

        # Remove www. prefix
        if hostname.startswith('www.'):
            hostname = hostname[4:]

        # Basic validation
        if '.' not in hostname:
            return None
        if len(hostname) > 253:
            return None

        # Minimum label length (each part must be >= 2 chars)
        parts = hostname.split('.')
        if any(len(p) < 2 for p in parts):
            return None

        # Must have a valid TLD
        if not has_valid_tld(hostname):
            return None

        return hostname.lower()
    except Exception:
        return None


def extract_tld(domain):
    """Extract TLD from a domain name."""
    if not domain:
        return None
    parts = domain.split('.')
    if len(parts) >= 3 and parts[-2] in ('co', 'com', 'org', 'net', 'ac', 'gov'):
        return '.' + '.'.join(parts[-2:])
    return '.' + parts[-1]


def is_skip_domain(domain):
    """Check if domain should be skipped (social media, major platforms)."""
    if not domain:
        return True
    for skip in SKIP_DOMAINS:
        if domain == skip or domain.endswith('.' + skip):
            return True
    return False


def resolve_redirect(url, timeout=5):
    """Follow redirects for shortened URLs. Returns final URL."""
    try:
        parsed = urlparse(url)
        if parsed.hostname in SHORTENERS:
            resp = requests.head(url, allow_redirects=True, timeout=timeout,
                                 headers={'User-Agent': 'GhostDomains/1.0'})
            return resp.url
    except Exception as e:
        logger.debug(f"Redirect resolve failed for {url}: {e}")
    return url


def extract_domains_from_text(text):
    """Full pipeline: extract URLs → resolve redirects → clean → filter → deduplicate."""
    urls = extract_urls(text)
    domains = set()

    for url in urls:
        # Resolve shorteners
        resolved = resolve_redirect(url)
        domain = clean_domain(resolved)

        if domain and not is_skip_domain(domain):
            domains.add(domain)

    return list(domains)
