import { Search, LayoutGrid, List, Columns3 } from 'lucide-react';

export default function FilterBar({ filters, onFilterChange, view, onViewChange }) {
  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <div className="filter-bar">
      <div className="search-input-wrapper">
        <Search />
        <input
          type="text"
          className="search-input"
          placeholder="Search domains..."
          value={filters.search || ''}
          onChange={(e) => handleChange('search', e.target.value)}
        />
      </div>

      <input
        type="date"
        className="filter-date"
        value={filters.date || ''}
        onChange={(e) => handleChange('date', e.target.value)}
      />

      <select
        className="filter-select"
        value={filters.min_da || ''}
        onChange={(e) => handleChange('min_da', e.target.value ? Number(e.target.value) : '')}
      >
        <option value="">Min DA</option>
        <option value="10">DA ≥ 10</option>
        <option value="20">DA ≥ 20</option>
        <option value="30">DA ≥ 30</option>
        <option value="40">DA ≥ 40</option>
        <option value="50">DA ≥ 50</option>
      </select>

      <select
        className="filter-select"
        value={filters.min_pa || ''}
        onChange={(e) => handleChange('min_pa', e.target.value ? Number(e.target.value) : '')}
      >
        <option value="">Min PA</option>
        <option value="10">PA ≥ 10</option>
        <option value="20">PA ≥ 20</option>
        <option value="30">PA ≥ 30</option>
        <option value="40">PA ≥ 40</option>
        <option value="50">PA ≥ 50</option>
      </select>

      <select
        className="filter-select"
        value={filters.source || ''}
        onChange={(e) => handleChange('source', e.target.value)}
      >
        <option value="">All Sources</option>
        <option value="youtube">YouTube</option>
        <option value="zone_file">Zone File</option>
        <option value="ct_log">CT Log</option>
        <option value="feed">Feed</option>
        <option value="manual">Manual</option>
      </select>

      <div className="view-toggle">
        <button
          className={view === 'list' ? 'active' : ''}
          onClick={() => onViewChange('list')}
          title="List view"
        >
          <List size={16} />
        </button>
        <button
          className={view === 'grid' ? 'active' : ''}
          onClick={() => onViewChange('grid')}
          title="Grid view"
        >
          <LayoutGrid size={16} />
        </button>
        <button
          className={view === 'compact' ? 'active' : ''}
          onClick={() => onViewChange('compact')}
          title="Compact view"
        >
          <Columns3 size={16} />
        </button>
      </div>
    </div>
  );
}
