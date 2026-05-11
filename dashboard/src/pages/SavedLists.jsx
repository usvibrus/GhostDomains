import { Bookmark, Plus } from 'lucide-react';

export default function SavedLists() {
  const mockLists = [
    { id: 1, name: 'High Priority Domains', count: 24, created: '2026-05-01' },
    { id: 2, name: 'Tech Niche Domains', count: 12, created: '2026-05-05' },
    { id: 3, name: 'Potential Blog Domains', count: 8, created: '2026-05-08' },
  ];

  return (
    <>
      <div className="top-header">
        <h1 className="page-title">Saved Lists</h1>
        <div className="header-actions">
          <button className="action-btn primary">
            <Plus size={16} /> New List
          </button>
        </div>
      </div>

      <div className="page-container">
        <div className="detail-grid animate-slide-up">
          {mockLists.map((list) => (
            <div className="detail-card" key={list.id} style={{ cursor: 'pointer', transition: 'all 0.2s' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 'var(--radius-md)',
                  background: 'rgba(0, 212, 170, 0.1)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', color: 'var(--accent-primary)'
                }}>
                  <Bookmark size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1rem', margin: 0, color: 'var(--text-primary)', textTransform: 'none', letterSpacing: 0 }}>
                    {list.name}
                  </h3>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Created {list.created}
                  </span>
                </div>
              </div>
              <div className="detail-row">
                <span className="label">Domains</span>
                <span className="value">{list.count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
