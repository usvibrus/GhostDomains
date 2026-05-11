import { useState } from 'react';
import { Search, Globe, Loader2 } from 'lucide-react';
import { lookupDomain } from '../api';

export default function DomainSearch() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    setResult(null);
    try {
      const res = await lookupDomain(query.trim());
      setResult(res.domain || res);
    } catch (err) {
      setError(err.message || 'Failed to look up domain');
    } finally {
      setSearching(false);
    }
  };

  return (
    <>
      <div className="top-header">
        <h1 className="page-title">Domain Search</h1>
      </div>

      <div className="page-container">
        <div className="detail-card animate-fade-in" style={{ maxWidth: 700, margin: '0 auto' }}>
          <h3 style={{ marginBottom: 24, textAlign: 'center', fontSize: '1rem' }}>
            Check any domain's expiry status & metrics
          </h3>

          <form onSubmit={handleSearch} style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
            <div className="search-input-wrapper" style={{ flex: 1, maxWidth: 'none' }}>
              <Search />
              <input
                type="text"
                className="search-input"
                placeholder="Enter domain name (e.g. example.com)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{ fontSize: '1rem', padding: '14px 14px 14px 44px' }}
              />
            </div>
            <button
              type="submit"
              className="action-btn primary"
              disabled={searching}
              style={{ minWidth: 120 }}
            >
              {searching ? <Loader2 size={16} className="spin" /> : 'Search'}
            </button>
          </form>

          {error && (
            <div className="animate-slide-up" style={{ color: 'var(--accent-red)', textAlign: 'center', marginBottom: 16 }}>
              {error}
            </div>
          )}

          {result && (
            <div className="animate-slide-up">
              <div className="detail-row">
                <span className="label">Domain</span>
                <span className="value">{result.domain}</span>
              </div>
              {result.message ? (
                <div className="detail-row">
                  <span className="label">Info</span>
                  <span className="value" style={{ color: 'var(--text-muted)' }}>{result.message}</span>
                </div>
              ) : (
                <>
                  <div className="detail-row">
                    <span className="label">Status</span>
                    <span className="value" style={{ color: result.is_expired ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                      {result.is_expired ? '● Expired' : '● Active'}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="label">WHOIS Status</span>
                    <span className="value">{result.whois_status || '—'}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Expiry Date</span>
                    <span className="value">{result.expiry_date || '—'}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">Registrar</span>
                    <span className="value">{result.registrar || '—'}</span>
                  </div>
                  <div className="detail-row">
                    <span className="label">DNS Resolves</span>
                    <span className="value">{result.dns_resolves ? 'Yes' : 'No'}</span>
                  </div>
                </>
              )}
            </div>
          )}

          {!result && !searching && !error && (
            <div className="empty-state" style={{ padding: '40px 20px' }}>
              <Globe size={48} />
              <h3>Enter a domain to check</h3>
              <p>We'll look up its WHOIS status, expiry date, and more.</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
