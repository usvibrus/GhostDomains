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
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const PER_PAGE = 20;

  useEffect(() => {
    setLoading(true);
    fetchDomains({ ...filters, page, per_page: PER_PAGE })
      .then((res) => {
        setDomains(res.data || []);
        setTotalPages(res.total_pages || 1);
        setTotal(res.total || 0);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [filters, page]);

  // Reset to page 1 when filters change
  const handleFilterChange = (newFilters) => {
    setPage(1);
    setFilters(newFilters);
  };

  return (
    <>
      <div className="top-header">
        <h1 className="page-title">Dashboard Overview</h1>
        <div className="header-actions">
          <button className="header-btn" title="Notifications">
            <Bell size={18} />
          </button>
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
            onFilterChange={handleFilterChange}
            view={view}
            onViewChange={setView}
          />
          <DomainTable
            domains={domains}
            loading={loading}
            page={page}
            totalPages={totalPages}
            total={total}
            perPage={PER_PAGE}
            onPageChange={setPage}
          />
        </div>
      </div>
    </>
  );
}
