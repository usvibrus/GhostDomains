import logging
import requests
from scraper.config import Config
from scraper.db import get_watchers, get_expiring_domains, create_alert, get_unsent_alerts_for_watcher, mark_alert_sent

logger = logging.getLogger(__name__)


def check_and_send_alerts():
    """Main alert pipeline: find expiring domains, match to watchers, send emails."""
    watchers = get_watchers()
    if not watchers:
        logger.info("No watchers configured. Skipping alerts.")
        return

    for watcher in watchers:
        domains = get_expiring_domains(
            days=watcher['notify_expiry_days'],
            min_score=watcher['min_da_threshold'],
        )
        for d in domains:
            create_alert(d['id'], watcher['id'], 'expiry_soon')

        unsent = get_unsent_alerts_for_watcher(watcher['id'])
        if unsent:
            _send_alert_email(watcher['email'], unsent)
            for alert in unsent:
                mark_alert_sent(alert['id'])

    logger.info("Alert check complete")


def _send_alert_email(to_email, alerts):
    """Send alert email via Resend API."""
    if not Config.has_resend():
        logger.warning(f"Resend not configured. Would send {len(alerts)} alerts to {to_email}")
        return

    domain_lines = '\n'.join([
        f"  • {a['domain']} (score: {a.get('composite_score', 'N/A')})"
        for a in alerts[:20]
    ])

    try:
        resp = requests.post(
            'https://api.resend.com/emails',
            headers={'Authorization': f"Bearer {Config.RESEND_API_KEY}", 'Content-Type': 'application/json'},
            json={
                'from': Config.ALERT_FROM_EMAIL,
                'to': [to_email],
                'subject': f'GhostDomains Alert: {len(alerts)} domains expiring soon',
                'text': f"Hi,\n\nThe following domains are expiring soon:\n\n{domain_lines}\n\nView them at your GhostDomains dashboard.\n\n— GhostDomains",
            },
            timeout=10,
        )
        if resp.status_code in (200, 201):
            logger.info(f"Alert email sent to {to_email} ({len(alerts)} domains)")
        else:
            logger.error(f"Resend API error: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        logger.error(f"Email send failed: {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    check_and_send_alerts()
