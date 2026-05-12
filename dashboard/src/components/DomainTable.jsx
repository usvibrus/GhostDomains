import { useNavigate } from 'react-router-dom';
import { ArrowUpDown, ChevronUp, ChevronDown, ChevronLeft, ChevronRight, Bookmark, Download, Globe } from 'lucide-react';

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

function sourceLabel(source) {
  const map = {
    youtube: 'YouTube',
    zone_file: 'Zone File',
    ct_log: 'CT Log',
    feed: 'Feed',
    manual: 'Manual',
  };
  return map[source] || source;
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

  // Build page number array with ellipsis for large page counts
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
      <table className="data-table">
        <thead>
          <tr>
            <th>Domain Name</th>
            <th>Expiration Date</th>
            <th>DA</th>
            <th>PA</th>
            <th>TF</th>
            <th>Backlinks</th>
            <th>Archive Age</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {domains.map((d, idx) => (
            <tr
              key={d.id}
              onClick={() => navigate(`/domain/${d.id}`)}
              style={{ animationDelay: `${idx * 0.03}s` }}
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
                <div className="actions-cell" onClick={(e) => e.stopPropagation()}>
                  <button className="action-btn save" title="Add to Saved">
                    <Bookmark size={14} /> Save
                  </button>
                  <button className="action-btn export" title="Export">
                    <Download size={14} /> Export
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="table-footer">
        <span className="table-info">
          Showing {start}–{end} of {total} domains
        </span>
        <div className="pagination">
          {/* Prev */}
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
            className="pagination-btn"
            title="Previous page"
          >
            <ChevronLeft size={14} />
          </button>

          {/* Page numbers */}
          {getPageNumbers().map((p, i) =>
            p === '...'
              ? <span key={`ellipsis-${i}`} style={{ padding: '0 4px', color: 'var(--text-muted)' }}>…</span>
              : <button
                  key={p}
                  onClick={() => onPageChange(p)}
                  className={`pagination-btn ${p === page ? 'active' : ''}`}
                >
                  {p}
                </button>
          )}

          {/* Next */}
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page === totalPages}
            className="pagination-btn"
            title="Next page"
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </>
  );
}
