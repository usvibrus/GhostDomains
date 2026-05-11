import logging
import socket
import time
import requests
import dns.resolver
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


# ─── WHOIS Check ───

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((socket.timeout, ConnectionError, OSError)),
    reraise=True,
)
def whois_check(domain):
    """
    Check WHOIS data for a domain.
    Returns dict with expiry_date, registrar, status.
    Falls back to whoisit if python-whois fails.
    """
    result = {
        'expiry_date': None,
        'registrar': None,
        'whois_status': None,
        'whois_found': False,
    }

    # Primary: python-whois
    try:
        import whois
        w = whois.whois(domain)
        if w and w.domain_name:
            result['whois_found'] = True
            # expiry_date can be a list
            exp = w.expiration_date
            if isinstance(exp, list):
                exp = exp[0]
            if exp:
                result['expiry_date'] = exp.strftime('%Y-%m-%d') if hasattr(exp, 'strftime') else str(exp)

            result['registrar'] = w.registrar
            status = w.status
            if isinstance(status, list):
                status = status[0] if status else None
            if status:
                # Extract just the status name before the URL
                result['whois_status'] = status.split(' ')[0] if ' ' in str(status) else str(status)
            return result
    except Exception as e:
        logger.debug(f"python-whois failed for {domain}: {e}")

    # Domain not found in WHOIS — likely expired/available
    return result


# ─── DNS Check ───

def dns_check(domain):
    """
    Check if domain resolves via DNS.
    Returns True if A or AAAA records found.
    """
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5

        try:
            resolver.resolve(domain, 'A')
            return True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass

        try:
            resolver.resolve(domain, 'AAAA')
            return True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            pass

        return False
    except dns.resolver.NXDOMAIN:
        return False
    except Exception as e:
        logger.debug(f"DNS check failed for {domain}: {e}")
        return None  # Unknown — couldn't determine


# ─── HTTP Check ───

def http_check(domain, timeout=5):
    """
    Check HTTP status of domain.
    Returns status code or None on failure.
    """
    for scheme in ['https', 'http']:
        try:
            resp = requests.head(
                f'{scheme}://{domain}',
                timeout=timeout,
                allow_redirects=True,
                headers={'User-Agent': 'GhostDomains/1.0 (domain-checker)'},
            )
            return resp.status_code
        except requests.exceptions.SSLError:
            continue
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            logger.debug(f"HTTP check failed for {domain}: {e}")
            continue
    return None


# ─── Combined Check ───

def full_check(domain, delay=1.0):
    """
    Run all checks on a domain: WHOIS → DNS → HTTP.
    Returns combined result dict.
    """
    logger.info(f"Checking domain: {domain}")

    # WHOIS
    whois_result = whois_check(domain)
    time.sleep(delay)

    # DNS
    dns_resolves = dns_check(domain)
    time.sleep(0.5)

    # HTTP (only if DNS resolves)
    http_status = None
    if dns_resolves:
        http_status = http_check(domain)
        time.sleep(delay)

    # Determine if expired
    is_expired = False
    if not whois_result['whois_found'] and dns_resolves is False:
        is_expired = True
    elif whois_result.get('whois_status') in ('pendingDelete', 'redemptionPeriod'):
        is_expired = True
    elif dns_resolves is False and http_status is None:
        is_expired = True

    return {
        'expiry_date': whois_result.get('expiry_date'),
        'registrar': whois_result.get('registrar'),
        'whois_status': whois_result.get('whois_status'),
        'dns_resolves': dns_resolves,
        'http_status': http_status,
        'is_expired': is_expired,
    }
