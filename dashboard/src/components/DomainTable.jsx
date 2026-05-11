import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpDown, ChevronUp, ChevronDown, Bookmark, Download, Globe } from 'lucide-react';

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

export default function DomainTable({ domains, loading }) {
  const navigate = useNavigate();
  const [sortField, setSortField] = useState('score');
  const [sortDir, setSortDir] = useState('desc');

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  const sorted = [...domains].sort((a, b) => {
    let aVal, bVal;
    switch (sortField) {
      case 'domain': aVal = a.domain; bVal = b.domain; break;
      case 'expiry': aVal = a.expiry_date || ''; bVal = b.expiry_date || ''; break;
      case 'da': aVal = a.metrics.domain_authority; bVal = b.metrics.domain_authority; break;
      case 'pa': aVal = a.metrics.page_authority; bVal = b.metrics.page_authority; break;
      case 'tf': aVal = a.metrics.trust_flow; bVal = b.metrics.trust_flow; break;
      case 'backlinks': aVal = a.metrics.backlinks; bVal = b.metrics.backlinks; break;
      case 'archive': aVal = a.metrics.archive_age_days; bVal = b.metrics.archive_age_days; break;
      default: aVal = a.metrics.composite_score; bVal = b.metrics.composite_score;
    }
    if (typeof aVal === 'string') {
      return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ArrowUpDown size={12} className="sort-icon" />;
    return sortDir === 'asc'
      ? <ChevronUp size={12} className="sort-icon" />
      : <ChevronDown size={12} className="sort-icon" />;
  };

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

  return (
    <>
      <table className="data-table">
        <thead>
          <tr>
            <th className={sortField === 'domain' ? 'sorted' : ''} onClick={() => handleSort('domain')}>
              Domain Name <SortIcon field="domain" />
            </th>
            <th className={sortField === 'expiry' ? 'sorted' : ''} onClick={() => handleSort('expiry')}>
              Expiration Date <SortIcon field="expiry" />
            </th>
            <th className={sortField === 'da' ? 'sorted' : ''} onClick={() => handleSort('da')}>
              DA <SortIcon field="da" />
            </th>
            <th className={sortField === 'pa' ? 'sorted' : ''} onClick={() => handleSort('pa')}>
              PA <SortIcon field="pa" />
            </th>
            <th className={sortField === 'tf' ? 'sorted' : ''} onClick={() => handleSort('tf')}>
              TF <SortIcon field="tf" />
            </th>
            <th className={sortField === 'backlinks' ? 'sorted' : ''} onClick={() => handleSort('backlinks')}>
              Backlinks <SortIcon field="backlinks" />
            </th>
            <th className={sortField === 'archive' ? 'sorted' : ''} onClick={() => handleSort('archive')}>
              Archive Age <SortIcon field="archive" />
            </th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((d, idx) => (
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
                <span className={`metric-value ${getMetricClass(d.metrics.domain_authority)}`}>
                  {d.metrics.domain_authority}
                </span>
              </td>
              <td>
                <span className={`metric-value ${getMetricClass(d.metrics.page_authority)}`}>
                  {d.metrics.page_authority}
                </span>
              </td>
              <td>
                <span className={`metric-value ${getMetricClass(d.metrics.trust_flow, [20, 35])}`}>
                  {d.metrics.trust_flow}
                </span>
              </td>
              <td>
                <span className="metric-value">{d.metrics.backlinks.toLocaleString()}</span>
              </td>
              <td>{d.metrics.archive_age_days} days</td>
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
        <span className="table-info">Showing {sorted.length} of {sorted.length} domains</span>
        <div className="pagination">
          <button disabled>←</button>
          <button className="active">1</button>
          <button>2</button>
          <button>3</button>
          <button>→</button>
        </div>
      </div>
    </>
  );
}
