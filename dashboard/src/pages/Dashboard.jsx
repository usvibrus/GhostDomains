import { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';
import StatsCards from '../components/StatsCards';
import FilterBar from '../components/FilterBar';
import DomainTable from '../components/DomainTable';
import { fetchDomains } from '../api';

export default function Dashboard() {
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});
  const [view, setView] = useState('list');

  useEffect(() => {
    setLoading(true);
    fetchDomains(filters).then((res) => {
      setDomains(res.data);
      setLoading(false);
    });
  }, [filters]);

  return (
    <>
      <div className="top-header">
        <h1 className="page-title">Dashboard Overview</h1>
        <div className="header-actions">
          <button className="header-btn" title="Notifications">
            <Bell size={18} />
          </button>
          <div className="user-avatar">GD</div>
        </div>
      </div>

      <div className="page-container">
        <StatsCards />

        <div className="table-section animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <div className="table-header">
            <h2 className="table-title">Recent Domain Findings</h2>
          </div>
          <FilterBar
            filters={filters}
            onFilterChange={setFilters}
            view={view}
            onViewChange={setView}
          />
          <DomainTable domains={domains} loading={loading} />
        </div>
      </div>
    </>
  );
}
