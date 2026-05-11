import { useState } from 'react';
import { Bell, Plus, Mail, Trash2 } from 'lucide-react';

export default function Alerts() {
  const [email, setEmail] = useState('');
  const mockAlerts = [
    { id: 1, email: 'user@example.com', min_da: 30, tld_filter: '.com, .net', notify_days: 30 },
    { id: 2, email: 'team@company.io', min_da: 50, tld_filter: null, notify_days: 14 },
  ];

  return (
    <>
      <div className="top-header">
        <h1 className="page-title">Alerts</h1>
      </div>

      <div className="page-container">
        {/* Add new watcher */}
        <div className="detail-card animate-fade-in" style={{ marginBottom: 24 }}>
          <h3>Add Email Alert</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 20 }}>
            Get notified when high-value expired domains are discovered.
          </p>
          <form style={{ display: 'flex', gap: 12 }} onSubmit={(e) => e.preventDefault()}>
            <div className="search-input-wrapper" style={{ flex: 1, maxWidth: 400 }}>
              <Mail size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="email"
                className="search-input"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <select className="filter-select">
              <option value="20">Min DA ≥ 20</option>
              <option value="30">Min DA ≥ 30</option>
              <option value="50">Min DA ≥ 50</option>
            </select>
            <select className="filter-select">
              <option value="30">30 days before expiry</option>
              <option value="14">14 days before expiry</option>
              <option value="7">7 days before expiry</option>
            </select>
            <button className="action-btn primary">
              <Plus size={16} /> Add Alert
            </button>
          </form>
        </div>

        {/* Existing watchers */}
        <div className="table-section animate-slide-up">
          <div className="table-header">
            <h2 className="table-title">Active Alerts</h2>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Min DA</th>
                <th>TLD Filter</th>
                <th>Notify Before</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {mockAlerts.map((a) => (
                <tr key={a.id}>
                  <td><span className="domain-name">{a.email}</span></td>
                  <td><span className="metric-value">{a.min_da}</span></td>
                  <td>{a.tld_filter || 'All TLDs'}</td>
                  <td>{a.notify_days} days</td>
                  <td>
                    <button className="action-btn export" style={{ color: 'var(--accent-red)' }}>
                      <Trash2 size={14} /> Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
