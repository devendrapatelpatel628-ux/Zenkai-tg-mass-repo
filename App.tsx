import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import LoginForm from './components/LoginForm';
import Dashboard from './components/Dashboard';
import ProxyManager from './components/ProxyManager';
import ReportManager from './components/ReportManager';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import AccountPool from './components/AccountPool';
import EvidenceCollector from './components/EvidenceCollector';

type View = 'dashboard' | 'login' | 'proxies' | 'reports' | 'analytics' | 'pool' | 'evidence';

export default function App() {
  const [view, setView] = useState<View>('dashboard');

  const renderView = () => {
    switch (view) {
      case 'dashboard':
        return <Dashboard onAddAccount={() => setView('login')} onManageProxies={() => setView('proxies')} onManageReports={() => setView('reports')} onViewAnalytics={() => setView('analytics')} onViewPool={() => setView('pool')} onViewEvidence={() => setView('evidence')} />;
      case 'login':
        return <LoginForm onSuccess={() => setView('dashboard')} onBack={() => setView('dashboard')} />;
      case 'proxies':
        return <ProxyManager onBack={() => setView('dashboard')} />;
      case 'reports':
        return <ReportManager onBack={() => setView('dashboard')} />;
      case 'analytics':
        return <AnalyticsDashboard onBack={() => setView('dashboard')} />;
      case 'pool':
        return <AccountPool onBack={() => setView('dashboard')} />;
      case 'evidence':
        return <EvidenceCollector onBack={() => setView('dashboard')} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-white selection:bg-sky-500/30">
      <div className="fixed inset-0 pointer-events-none opacity-[0.03]" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")` }} />
      <div className="fixed inset-0 pointer-events-none opacity-[0.02]" style={{ backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`, backgroundSize: '60px 60px' }} />

      <AnimatePresence mode="wait">
        <motion.div key={view} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
          {renderView()}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
