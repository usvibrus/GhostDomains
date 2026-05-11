import sys
import os
import csv
import io
import logging

# Add parent directory so we can import scraper modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, jsonify, request, Response, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from scraper.db import (
    init_db, get_domains, get_domain_by_id, get_stats, get_chart_data,
    save_domain, save_metrics, get_saved_lists, create_saved_list,
    add_domain_to_list, get_saved_list_domains, get_watchers,
    create_watcher, delete_watcher, domain_exists
)
from scraper.config import Config

logger = logging.getLogger(__name__)

# ─── App Setup ───

STATIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'dist')
IS_PRODUCTION = os.getenv('RAILWAY_ENVIRONMENT', '') != '' or os.getenv('PRODUCTION', '') == '1'

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='')

# CORS: restrictive in production, open in dev
if IS_PRODUCTION:
    allowed_origins = [
        'https://ghostedomains.site',
        'https://www.ghostedomains.site',
    ]
    CORS(app, origins=allowed_origins)
else:
    CORS(app, origins="*")

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)


# ─── Middleware ───

@app.before_request
def check_api_key():
    """Optional API key authentication. Skip for dev if no key set."""
    # Skip auth for static files and health
    if not request.path.startswith('/api/'):
        return
    if request.endpoint == 'health':
        return
    if Config.API_SECRET_KEY == 'dev-secret-key' and not IS_PRODUCTION:
        return  # Skip auth in dev mode
    # In production, check API key for write operations
    if request.method in ('POST', 'PUT', 'DELETE'):
        key = request.headers.get('X-API-Key', '')
        if key != Config.API_SECRET_KEY:
            return jsonify({'error': 'Unauthorized'}), 401


# ─── Health Check ───

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'ghostdomains-api',
        'production': IS_PRODUCTION,
    })


# ─── Domain Endpoints ───

@app.route('/api/domains')
def list_domains():
    """Paginated, filterable domain list."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort = request.args.get('sort', 'composite_score')
    order = request.args.get('order', 'desc')
    min_da = request.args.get('min_da', None, type=float)
    min_pa = request.args.get('min_pa', None, type=float)
    tld = request.args.get('tld', None)
    source = request.args.get('source', None)
    is_expired_param = request.args.get('is_expired', 'true')
    search = request.args.get('search', None)
    expiry_within = request.args.get('expiry_within', None, type=int)

    # Default to showing only expired domains
    is_expired = is_expired_param.lower() in ('true', '1', 'yes')
    if is_expired_param.lower() in ('false', '0', 'no', 'all'):
        is_expired = None  # Show all when explicitly set to false/all

    per_page = min(per_page, 100)  # Cap at 100

    result = get_domains(
        page=page, per_page=per_page, sort=sort, order=order,
        min_da=min_da, min_pa=min_pa, tld=tld, source=source,
        is_expired=is_expired, search=search, expiry_within=expiry_within,
    )
    return jsonify(result)


@app.route('/api/domains/<int:domain_id>')
def domain_detail(domain_id):
    """Full domain details by ID."""
    domain = get_domain_by_id(domain_id)
    if not domain:
        return jsonify({'error': 'Domain not found'}), 404
    return jsonify(domain)


@app.route('/api/domains/export')
def export_domains():
    """Export domains as CSV or JSON."""
    fmt = request.args.get('format', 'json')
    result = get_domains(
        is_expired=True,
        page=1, per_page=10000,
        sort=request.args.get('sort', 'composite_score'),
        order=request.args.get('order', 'desc'),
        min_da=request.args.get('min_da', None, type=float),
        min_pa=request.args.get('min_pa', None, type=float),
        tld=request.args.get('tld', None),
        source=request.args.get('source', None),
        search=request.args.get('search', None),
    )

    if fmt == 'csv':
        output = io.StringIO()
        if result['data']:
            flat_data = []
            for d in result['data']:
                flat = {**d}
                metrics = flat.pop('metrics', {})
                flat.update(metrics)
                flat_data.append(flat)

            writer = csv.DictWriter(output, fieldnames=flat_data[0].keys())
            writer.writeheader()
            writer.writerows(flat_data)

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=ghostdomains_export.csv'}
        )
    else:
        return jsonify(result)


@app.route('/api/domains/lookup', methods=['POST'])
@limiter.limit("10 per minute")
def lookup_domain():
    """Manual domain lookup — check a domain's status."""
    data = request.get_json()
    if not data or 'domain' not in data:
        return jsonify({'error': 'Missing domain field'}), 400

    domain_name = data['domain'].strip().lower()

    existing = domain_exists(domain_name)
    if existing:
        domain = get_domain_by_id(existing['id'])
        return jsonify({'source': 'cache', 'domain': domain})

    return jsonify({
        'source': 'live',
        'domain': {
            'domain': domain_name,
            'is_expired': None,
            'whois_status': 'checking...',
            'message': 'Full WHOIS/DNS check requires scraper pipeline. Domain not yet in database.'
        }
    })


# ─── Stats Endpoints ───

@app.route('/api/stats')
def stats():
    """Dashboard summary statistics."""
    return jsonify(get_stats())


@app.route('/api/stats/chart')
def stats_chart():
    """Daily domain counts for sparkline chart."""
    days = request.args.get('days', 30, type=int)
    return jsonify(get_chart_data(days=days))


# ─── Saved Lists ───

@app.route('/api/lists', methods=['GET'])
def list_saved_lists():
    return jsonify(get_saved_lists())


@app.route('/api/lists', methods=['POST'])
def create_list():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Missing name field'}), 400
    list_id = create_saved_list(data['name'])
    return jsonify({'id': list_id, 'name': data['name']}), 201


@app.route('/api/lists/<int:list_id>/domains', methods=['GET'])
def list_domains_in_list(list_id):
    return jsonify(get_saved_list_domains(list_id))


@app.route('/api/lists/<int:list_id>/domains', methods=['POST'])
def add_to_list(list_id):
    data = request.get_json()
    if not data or 'domain_id' not in data:
        return jsonify({'error': 'Missing domain_id field'}), 400
    add_domain_to_list(list_id, data['domain_id'], data.get('notes', ''))
    return jsonify({'status': 'added'}), 201


# ─── Watchers ───

@app.route('/api/watchers', methods=['GET'])
def list_watchers():
    return jsonify(get_watchers())


@app.route('/api/watchers', methods=['POST'])
def create_new_watcher():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Missing email field'}), 400
    watcher_id = create_watcher(
        email=data['email'],
        min_da=data.get('min_da', 20),
        tld_filter=data.get('tld_filter'),
        notify_days=data.get('notify_days', 30),
    )
    return jsonify({'id': watcher_id}), 201


@app.route('/api/watchers/<int:watcher_id>', methods=['DELETE'])
def remove_watcher(watcher_id):
    delete_watcher(watcher_id)
    return jsonify({'status': 'deleted'})


# ─── Serve React SPA ───

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    """Serve React SPA — API routes are handled above, everything else goes to index.html."""
    if path and os.path.exists(os.path.join(STATIC_DIR, path)):
        return send_from_directory(STATIC_DIR, path)
    index_path = os.path.join(STATIC_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(STATIC_DIR, 'index.html')
    return jsonify({
        'error': 'Dashboard not built yet. Run: cd dashboard && npm run build',
        'api': 'API is running. Try /api/health'
    }), 200


# ─── Error Handlers ───

@app.errorhandler(404)
def not_found(e):
    # If it's an API request, return JSON
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    # Otherwise serve SPA
    index_path = os.path.join(STATIC_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(STATIC_DIR, 'index.html')
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(429)
def rate_limited(e):
    return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500


# ─── Startup ───

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    init_db()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=not IS_PRODUCTION)
