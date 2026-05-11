import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Globe, Calendar, Shield, ShieldAlert,
  ExternalLink, Bookmark, Download, Youtube
} from 'lucide-react';
import { fetchDomainById } from '../api';

function getMetricClass(value, max = 100) {
  const pct = (value / max) * 100;
  if (pct >= 50) return 'high';
  if (pct >= 30) return 'medium';
  return 'low';
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
  });
}

function sourceLabel(s) {
  return { youtube: 'YouTube', zone_file: 'Zone File', ct_log: 'CT Log', feed: 'Feed', manual: 'Manual' }[s] || s;
}

export default function DomainDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [domain, setDomain] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDomainById(id).then((d) => {
      setDomain(d);
      setLoading(false);
    });
  }, [id]);

  if (loading) {
    return (
      <div className="page-container">
        <div className="skeleton" style={{ height: 40, width: 200, marginBottom: 24 }} />
        <div className="skeleton" style={{ height: 300 }} />
      </div>
    );
  }

  if (!domain) {
    return (
      <div className="page-container">
        <div className="detail-back" onClick={() => navigate('/')}>
          <ArrowLeft size={16} /> Back to Dashboard
        </div>
        <div className="empty-state">
          <Globe size={48} />
          <h3>Domain not found</h3>
          <p>This domain doesn't exist in our database.</p>
        </div>
      </div>
    );
  }

  const m = domain.metrics;
  const metrics = [
    { label: 'Domain Authority', value: m.domain_authority, max: 100 },
    { label: 'Page Authority', value: m.page_authority, max: 100 },
    { label: 'Trust Flow', value: m.trust_flow, max: 100 },
    { label: 'Composite Score', value: m.composite_score, max: 100 },
  ];

  return (
    <>
      <div className="top-header">
        <h1 className="page-title">Domain Details</h1>
      </div>

      <div className="page-container">
        <div className="detail-back" onClick={() => navigate('/')}>
          <ArrowLeft size={16} /> Back to Dashboard
        </div>

        <div className="detail-header animate-fade-in">
          <div>
            <h1 className="detail-domain-name">{domain.domain}</h1>
            <div style={{ display: 'flex', gap: 12, marginTop: 8, alignItems: 'center' }}>
              <span className={`source-badge ${domain.discovery_source}`}>
                {domain.discovery_source === 'youtube' && <Youtube size={12} />}
                {sourceLabel(domain.discovery_source)}
              </span>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Found on {formatDate(domain.first_found_at)}
              </span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <button className="action-btn save"><Bookmark size={14} /> Add to Saved</button>
            <button className="action-btn export"><Download size={14} /> Export</button>
          </div>
        </div>

        <div className="detail-grid animate-slide-up" style={{ animationDelay: '0.1s' }}>
          {/* WHOIS Info */}
          <div className="detail-card">
            <h3>WHOIS Information</h3>
            <div className="detail-row">
              <span className="label">Status</span>
              <span className="value" style={{ color: domain.is_expired ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                {domain.is_expired ? '● Expired' : '● Active'}
              </span>
            </div>
            <div className="detail-row">
              <span className="label">WHOIS Status</span>
              <span className="value">{domain.whois_status || '—'}</span>
            </div>
            <div className="detail-row">
              <span className="label">Expiry Date</span>
              <span className="value"><Calendar size={14} style={{ marginRight: 6 }} />{formatDate(domain.expiry_date)}</span>
            </div>
            <div className="detail-row">
              <span className="label">Registrar</span>
              <span className="value">{domain.registrar || '—'}</span>
            </div>
            <div className="detail-row">
              <span className="label">TLD</span>
              <span className="value">{domain.tld}</span>
            </div>
            <div className="detail-row">
              <span className="label">DNS Resolves</span>
              <span className="value">{domain.dns_resolves ? 'Yes' : 'No'}</span>
            </div>
          </div>

          {/* SEO Metrics */}
          <div className="detail-card">
            <h3>SEO Metrics</h3>
            {metrics.map((met) => (
              <div className="metric-bar" key={met.label}>
                <span className="metric-label">{met.label}</span>
                <div className="bar-track">
                  <div
                    className={`bar-fill ${getMetricClass(met.value, met.max)}`}
                    style={{ width: `${(met.value / met.max) * 100}%` }}
                  />
                </div>
                <span className="metric-val">{met.value}</span>
              </div>
            ))}
            <div className="detail-row" style={{ marginTop: 12 }}>
              <span className="label">Backlinks</span>
              <span className="value">{m.backlinks.toLocaleString()}</span>
            </div>
          </div>

          {/* Archive & Safety */}
          <div className="detail-card">
            <h3>Archive & Safety</h3>
            <div className="detail-row">
              <span className="label">Wayback Snapshots</span>
              <span className="value">{m.wayback_snapshots.toLocaleString()}</span>
            </div>
            <div className="detail-row">
              <span className="label">Archive Age</span>
              <span className="value">{m.archive_age_days} days</span>
            </div>
            <div className="detail-row">
              <span className="label">Google Safe Browsing</span>
              <span className="value" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {m.google_safe
                  ? <><Shield size={14} color="var(--accent-green)" /> Safe</>
                  : <><ShieldAlert size={14} color="var(--accent-red)" /> Unsafe</>
                }
              </span>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="detail-card">
            <h3>Quick Actions</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <a
                href={`https://web.archive.org/web/*/${domain.domain}`}
                target="_blank"
                rel="noopener noreferrer"
                className="action-btn primary"
                style={{ textAlign: 'center', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
              >
                <ExternalLink size={16} /> View on Wayback Machine
              </a>
              <a
                href={`https://www.godaddy.com/domainsearch/find?domainToCheck=${domain.domain}`}
                target="_blank"
                rel="noopener noreferrer"
                className="action-btn export"
                style={{ textAlign: 'center', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '10px 20px' }}
              >
                Check on GoDaddy
              </a>
              <a
                href={`https://www.namecheap.com/domains/registration/results/?domain=${domain.domain}`}
                target="_blank"
                rel="noopener noreferrer"
                className="action-btn export"
                style={{ textAlign: 'center', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '10px 20px' }}
              >
                Check on Namecheap
              </a>
              <a
                href={`https://www.dynadot.com/domain/search?domain=${domain.domain}`}
                target="_blank"
                rel="noopener noreferrer"
                className="action-btn export"
                style={{ textAlign: 'center', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '10px 20px' }}
              >
                Check on Dynadot
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
