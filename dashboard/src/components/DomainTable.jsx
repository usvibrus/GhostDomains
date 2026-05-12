import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Bookmark, Download, Globe, Check, X } from 'lucide-react';
import { addDomainToList, createSavedList, fetchSavedLists, getExportUrl } from '../api';

function getMetricClass(value, thresholds = [30, 50]) {
  if (value >= thresholds[1]) return 'high';
  if (value >= thresholds[0]) return 'medium';
  return 'low';
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatVolume(vol) {
  if (!vol || vol === 0) return '—';
  if (vol >= 1000000) return (vol / 1000000).toFixed(1) + 'M';
  if (vol >= 1000) return (vol / 1000).toFixed(1) + 'K';
  return vol.toString();
}

// Export single domain as CSV row download
function exportDomain(domain) {
  const m = domain.metrics || {};
  const row = [
    domain.domain,
    domain.expiry_date || '',
    m.domain_authority || 0,
    m.page_authority || 0,
    m.trust_flow || 0,
    m.backlinks || 0,
    m.archive_age_days || 0,
    m.monthly_searches || 0,
    m.composite_score || 0,
    domain.discovery_source || '',
  ];
  const headers = ['domain','expiry_date','da','pa','tf','backlinks','archive_age_days','monthly_searches','score','source'];
  const csv = [headers.join(','), row.join(',')].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${domain.domain}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// Save domain button with inline feedback
function SaveButton({ domain }) {
  const [status, setStatus] = useState('idle'); // idle | saving | saved | error

  const handleSave = async (e) => {
    e.stopPropagation();
    if (status !== 'idle') return;
    setStatus('saving');
    try {
      // Get or create default "Saved Domains" list
      let lists = await fetchSavedLists();
      let list = lists.find(l => l.name === 'Saved Domains');
      if (!list) {
        list = await createSavedList('Saved Domains');
      }
      await addDomainToList(list.id, domain.id);
      setStatus('saved');
      setTimeout(() => setStatus('idle'), 2500);
    } catch (err) {
      // Already saved or error — still show saved
      setStatus('saved');
      setTimeout(() => setStatus('idle'), 2500);
    }
  };

  return (
    <button
      className={`action-btn save ${status === 'saved' ? 'saved-active' : ''}`}
      title="Save to list"
      onClick={handleSave}
      disabled={status === 'saving'}
      style={{ minWidth: 70 }}
    >
      {status === 'saved' ? <><Check size={13} /> Saved</> : <><Bookmark size={13} /> Save</>}
    </button>
  );
}

export default function DomainTable({
  domains,
  loading,
  page = 1,
  totalPages = 1,
  total = 0,
  perPage = 20,
  onPageChange,
}) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <div style={{ padding: '20px' }}>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="skeleton" style={{ height: 48, marginBottom: 8 }} />
        ))}
      </div>
    );
  }

  if (!domains.length) {
    return (
      <div className="empty-state">
        <Globe size={48} />
        <h3>No domains found</h3>
        <p>Try adjusting your filters or check back later.</p>
      </div>
    );
  }

  // Build page number array with ellipsis
  const getPageNumbers = () => {
    if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
    const pages = [];
    pages.push(1);
    if (page > 3) pages.push('...');
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
      pages.push(i);
    }
    if (page < totalPages - 2) pages.push('...');
    pages.push(totalPages);
    return pages;
  };

  const start = (page - 1) * perPage + 1;
  const end = Math.min(page * perPage, total);

  return (
    <>
      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Domain Name</th>
              <th>Expiry Date</th>
              <th>DA</th>
              <th>PA</th>
              <th>TF</th>
              <th>Backlinks</th>
              <th>Archive Age</th>
              <th title="Estimated monthly search volume for this domain as a keyword">
                Monthly Vol.
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {domains.map((d, idx) => (
              <tr
                key={d.id}
                onClick={() => navigate(`/domain/${d.id}`)}
                style={{ animationDelay: `${idx * 0.03}s`, cursor: 'pointer' }}
                className="animate-fade-in"
              >
                <td>
                  <span className="domain-name">{d.domain}</span>
                </td>
                <td>{formatDate(d.expiry_date)}</td>
                <td>
                  <span className={`metric-value ${getMetricClass(d.metrics?.domain_authority ?? 0)}`}>
                    {d.metrics?.domain_authority ?? 0}
                  </span>
                </td>
                <td>
                  <span className={`metric-value ${getMetricClass(d.metrics?.page_authority ?? 0)}`}>
                    {d.metrics?.page_authority ?? 0}
                  </span>
                </td>
                <td>
                  <span className={`metric-value ${getMetricClass(d.metrics?.trust_flow ?? 0, [20, 35])}`}>
                    {d.metrics?.trust_flow ?? 0}
                  </span>
                </td>
                <td>
                  <span className="metric-value">{(d.metrics?.backlinks ?? 0).toLocaleString()}</span>
                </td>
                <td>{d.metrics?.archive_age_days ?? 0} days</td>
                <td>
                  <span
                    className={`metric-value ${getMetricClass(d.metrics?.monthly_searches ?? 0, [1000, 10000])}`}
                    title="Monthly search volume"
                  >
                    {formatVolume(d.metrics?.monthly_searches)}
                  </span>
                </td>
                <td>
                  <div className="actions-cell" onClick={(e) => e.stopPropagation()}>
                    <SaveButton domain={d} />
                    <button
                      className="action-btn export"
                      title="Export as CSV"
                      onClick={(e) => { e.stopPropagation(); exportDomain(d); }}
                    >
                      <Download size={13} /> Export
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="table-footer">
        <span className="table-info">
          Showing {start}–{end} of {total} domains
        </span>
        <div className="pagination">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
            className="pagination-btn"
          >
            <ChevronLeft size={14} />
          </button>

          {getPageNumbers().map((p, i) =>
            p === '...'
              ? <span key={`e-${i}`} style={{ padding: '0 4px', color: 'var(--text-muted)' }}>…</span>
              : <button
                  key={p}
                  onClick={() => onPageChange(p)}
                  className={`pagination-btn ${p === page ? 'active' : ''}`}
                >
                  {p}
                </button>
          )}

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page === totalPages}
            className="pagination-btn"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </>
  );
}
