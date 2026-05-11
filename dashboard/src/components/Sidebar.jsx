import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Search, SlidersHorizontal, Bookmark,
  Bell, FileText, Settings, HelpCircle, Ghost
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/search', icon: Search, label: 'Domain Search' },
  { to: '/filters', icon: SlidersHorizontal, label: 'Filters' },
  { to: '/saved', icon: Bookmark, label: 'Saved Lists' },
  { to: '/alerts', icon: Bell, label: 'Alerts', badge: '3' },
  { to: '/reports', icon: FileText, label: 'Reports' },
];

const bottomItems = [
  { to: '/settings', icon: Settings, label: 'Settings' },
  { to: '/help', icon: HelpCircle, label: 'Help & Support' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">
          <Ghost size={20} />
        </div>
        <div className="logo-text">
          <span className="brand-name">GHOST</span>
          <span className="brand-tag">Domains</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <span className="nav-section-title">Main Menu</span>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <item.icon size={20} />
            <span>{item.label}</span>
            {item.badge && <span className="nav-badge">{item.badge}</span>}
          </NavLink>
        ))}

        <span className="nav-section-title" style={{ marginTop: 'auto' }}>System</span>
        {bottomItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
