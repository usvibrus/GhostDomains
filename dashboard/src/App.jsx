import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import DomainDetail from './pages/DomainDetail';
import DomainSearch from './pages/DomainSearch';
import SavedLists from './pages/SavedLists';
import Alerts from './pages/Alerts';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/domain/:id" element={<DomainDetail />} />
            <Route path="/search" element={<DomainSearch />} />
            <Route path="/saved" element={<SavedLists />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/filters" element={<Dashboard />} />
            <Route path="/reports" element={<Dashboard />} />
            <Route path="/settings" element={<Dashboard />} />
            <Route path="/help" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
