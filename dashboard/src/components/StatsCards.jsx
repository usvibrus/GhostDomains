import { useEffect, useState } from 'react';
import { BarChart3, TrendingUp } from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { fetchStats, fetchChartData } from '../api';

function formatNumber(num) {
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (num >= 1_000) return num.toLocaleString();
  return String(num);
}

export default function StatsCards() {
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    fetchStats().then(setStats);
    fetchChartData().then(setChartData);
  }, []);

  if (!stats) {
    return (
      <div className="stats-grid">
        <div className="stat-card"><div className="skeleton" style={{ height: 120 }} /></div>
        <div className="stat-card"><div className="skeleton" style={{ height: 120 }} /></div>
      </div>
    );
  }

  return (
    <div className="stats-grid stagger-children">
      <div className="stat-card animate-fade-in">
        <div className="card-header">
          <span className="card-label">Expired Domains Found Today</span>
          <div className="card-icon">
            <BarChart3 size={20} />
          </div>
        </div>
        <div className="card-value animate-count">{formatNumber(stats.found_today)}</div>
        <span className={`card-change ${stats.found_today_change >= 0 ? 'positive' : 'negative'}`}>
          <TrendingUp size={14} />
          {stats.found_today_change >= 0 ? '+' : ''}{stats.found_today_change}%
        </span>
        <div className="card-subtitle">Compared to yesterday</div>
      </div>

      <div className="stat-card accent-blue animate-fade-in">
        <div className="card-header">
          <span className="card-label">Total Expired Domains Found</span>
          <div className="card-icon">
            <TrendingUp size={20} />
          </div>
        </div>
        <div className="card-value animate-count">{formatNumber(stats.total_found)}</div>
        <div className="card-subtitle">{stats.growth_label}</div>
        <div className="sparkline-container">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#0984e3" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#0984e3" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area
                type="monotone"
                dataKey="count"
                stroke="#0984e3"
                strokeWidth={2}
                fill="url(#sparkGradient)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
