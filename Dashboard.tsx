import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Trash2,
  User,
  Users,
  Phone,
  Clock,
  Hash,
  LogOut,
  Settings,
  Wifi,
  WifiOff,
  ChevronDown,
  Copy,
  Check,
  Search,
  LayoutGrid,
  List,
  RefreshCw,
  Server,
  Globe,
  Flag,
  BarChart3,
  Camera,
} from 'lucide-react';
import { api, TelegramAccountApi, ProxyStats } from '../api';
import GlowButton from './GlowButton';
import TelegramLogo from './TelegramLogo';

interface DashboardProps {
  onAddAccount: () => void;
  onManageProxies: () => void;
  onManageReports: () => void;
  onViewAnalytics: () => void;
  onViewPool: () => void;
  onViewEvidence: () => void;
}

export default function Dashboard({ onAddAccount, onManageProxies, onManageReports, onViewAnalytics, onViewPool, onViewEvidence }: DashboardProps) {
  const [accounts, setAccounts] = useState<TelegramAccountApi[]>([]);
  const [loading, setLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [proxyStats, setProxyStats] = useState<ProxyStats | null>(null);

  const fetchAccounts = useCallback(async () => {
    const online = await api.healthCheck();
    setBackendOnline(online);

    if (!online) {
      setLoading(false);
      return;
    }

    try {
      const result = await api.getAccounts();
      if (result.success) {
        setAccounts(result.accounts);
      }
      
      // Fetch proxy stats
      const proxyResult = await api.getProxies();
      if (proxyResult.success) {
        setProxyStats(proxyResult.stats);
      }
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAccounts();
    setRefreshing(false);
  };

  const handleDelete = async (id: string) => {
    if (deleteConfirm === id) {
      setDeletingId(id);
      const result = await api.deleteAccount(id);
      if (result.success) {
        setAccounts((prev) => prev.filter((a) => a.id !== id));
      }
      setDeletingId(null);
      setDeleteConfirm(null);
      setExpandedId(null);
    } else {
      setDeleteConfirm(id);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const filteredAccounts = accounts.filter(
    (a) =>
      a.phone.includes(searchQuery) ||
      a.firstName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (a.username && a.username.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const statusColors = {
    online: 'bg-emerald-500',
    recently: 'bg-amber-500',
    offline: 'bg-slate-500',
  };

  // Backend offline state
  if (backendOnline === false) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/3 w-96 h-96 bg-red-500/5 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-orange-500/5 rounded-full blur-3xl" />
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative bg-slate-900/80 backdrop-blur-2xl border border-red-500/20 rounded-3xl p-8 max-w-md text-center"
        >
          <div className="absolute -top-px left-10 right-10 h-px bg-gradient-to-r from-transparent via-red-500/50 to-transparent" />

          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center">
                <Server size={40} className="text-red-400" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-slate-900 flex items-center justify-center border-2 border-red-500/50">
                <WifiOff size={14} className="text-red-400" />
              </div>
            </div>
          </div>

          <h2 className="text-xl font-bold text-white mb-2">Backend Offline</h2>
          <p className="text-sm text-slate-400 mb-4">
            The Python backend server is not running. Follow these steps to start it:
          </p>

          <div className="bg-slate-800/50 rounded-xl p-4 mb-4 text-left space-y-3">
            <div>
              <p className="text-xs text-emerald-400 font-semibold mb-1">Step 1: Open Terminal</p>
              <code className="text-xs text-slate-300 font-mono block bg-black/30 p-2 rounded">
                cd backend
              </code>
            </div>
            <div>
              <p className="text-xs text-emerald-400 font-semibold mb-1">Step 2: Install & Run</p>
              <code className="text-xs text-slate-300 font-mono block bg-black/30 p-2 rounded">
                python run.py
              </code>
            </div>
            <div>
              <p className="text-xs text-emerald-400 font-semibold mb-1">Or with Docker:</p>
              <code className="text-xs text-slate-300 font-mono block bg-black/30 p-2 rounded">
                docker-compose up
              </code>
            </div>
          </div>
          
          <p className="text-xs text-slate-500 mb-4">
            Backend should run on <span className="text-sky-400">http://localhost:8000</span>
          </p>

          <GlowButton onClick={handleRefresh} className="w-full">
            <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            Retry Connection
          </GlowButton>
        </motion.div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <RefreshCw size={32} className="text-sky-400" />
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/3 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8"
        >
          <div className="flex items-center gap-4">
            <div className="relative">
              <TelegramLogo className="w-12 h-12" />
              <div className="absolute -inset-1 bg-sky-500/20 rounded-full blur-lg" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white">TeleManager</h1>
              <div className="flex items-center gap-2">
                <p className="text-sm text-slate-400">Manage your Telegram accounts</p>
                {backendOnline && (
                  <span className="flex items-center gap-1 text-xs text-emerald-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Live
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            {/* Refresh button */}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="p-2.5 bg-white/5 border border-white/10 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-all cursor-pointer disabled:opacity-50"
            >
              <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
            </button>

            {/* Search */}
            <div className="relative flex-1 md:w-64">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search accounts..."
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-sky-500/50 focus:ring-2 focus:ring-sky-500/20 transition-all text-sm"
              />
            </div>

            {/* View toggle */}
            <div className="flex bg-white/5 border border-white/10 rounded-xl overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2.5 transition-colors cursor-pointer ${
                  viewMode === 'grid' ? 'bg-sky-500/20 text-sky-400' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                <LayoutGrid size={16} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2.5 transition-colors cursor-pointer ${
                  viewMode === 'list' ? 'bg-sky-500/20 text-sky-400' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                <List size={16} />
              </button>
            </div>

            {/* Proxy Manager Button */}
            <button
              onClick={onManageProxies}
              className="p-2.5 bg-purple-500/10 border border-purple-500/20 rounded-xl text-purple-400 hover:bg-purple-500/20 transition-all cursor-pointer flex items-center gap-2"
              title="Manage Proxies"
            >
              <Globe size={16} />
              {proxyStats && proxyStats.available > 0 && (
                <span className="text-xs font-semibold">{proxyStats.available}</span>
              )}
            </button>

            {/* Report Manager Button */}
            <button
              onClick={onManageReports}
              className="p-2.5 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 hover:bg-red-500/20 transition-all cursor-pointer flex items-center gap-2"
              title="Report Manager"
            >
              <Flag size={16} />
            </button>

            {/* Analytics Button */}
            <button
              onClick={onViewAnalytics}
              className="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400 hover:bg-blue-500/20 transition-all cursor-pointer flex items-center gap-2"
              title="Analytics Dashboard"
            >
              <BarChart3 size={16} />
            </button>

            {/* Account Pool Button */}
            <button
              onClick={onViewPool}
              className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400 hover:bg-emerald-500/20 transition-all cursor-pointer flex items-center gap-2"
              title="Account Pool"
            >
              <Users size={16} />
            </button>

            {/* Evidence Button */}
            <button
              onClick={onViewEvidence}
              className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400 hover:bg-amber-500/20 transition-all cursor-pointer flex items-center gap-2"
              title="Evidence Collector"
            >
              <Camera size={16} />
            </button>

            <GlowButton onClick={onAddAccount}>
              <Plus size={18} />
              <span className="hidden sm:inline">Add Account</span>
            </GlowButton>
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
        >
          {[
            { label: 'Total Accounts', value: accounts.length, icon: User, color: 'sky' },
            {
              label: 'Online',
              value: accounts.filter((a) => a.status === 'online').length,
              icon: Wifi,
              color: 'emerald',
            },
            {
              label: 'Offline',
              value: accounts.filter((a) => a.status === 'offline').length,
              icon: WifiOff,
              color: 'slate',
            },
            {
              label: 'Recently',
              value: accounts.filter((a) => a.status === 'recently').length,
              icon: Clock,
              color: 'amber',
            },
          ].map((stat) => (
            <div
              key={stat.label}
              className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-4 text-center"
            >
              <div
                className={`inline-flex items-center justify-center w-10 h-10 rounded-xl mb-2 ${
                  stat.color === 'sky'
                    ? 'bg-sky-500/10 text-sky-400'
                    : stat.color === 'emerald'
                      ? 'bg-emerald-500/10 text-emerald-400'
                      : stat.color === 'amber'
                        ? 'bg-amber-500/10 text-amber-400'
                        : 'bg-slate-500/10 text-slate-400'
                }`}
              >
                <stat.icon size={18} />
              </div>
              <p className="text-2xl font-bold text-white">{stat.value}</p>
              <p className="text-xs text-slate-500">{stat.label}</p>
            </div>
          ))}
        </motion.div>

        {/* Accounts */}
        {filteredAccounts.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-3xl p-12 text-center"
          >
            <div className="relative inline-block mb-6">
              <div className="w-24 h-24 rounded-full bg-white/5 flex items-center justify-center">
                <User size={40} className="text-slate-600" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-sky-500 flex items-center justify-center">
                <Plus size={16} className="text-white" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No Accounts Yet</h3>
            <p className="text-sm text-slate-400 mb-6 max-w-sm mx-auto">
              Add your first Telegram account to get started. You'll need your API ID and Hash from
              my.telegram.org
            </p>
            <GlowButton onClick={onAddAccount}>
              <Plus size={18} />
              Add Your First Account
            </GlowButton>
          </motion.div>
        ) : (
          <div
            className={
              viewMode === 'grid'
                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                : 'space-y-3'
            }
          >
            <AnimatePresence>
              {filteredAccounts.map((account, index) => (
                <motion.div
                  key={account.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl overflow-hidden hover:border-white/10 transition-all duration-300 group"
                >
                  {/* Card header */}
                  <div className="p-5">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        {/* Avatar */}
                        <div className="relative">
                          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-sky-500/20">
                            {account.firstName[0]}
                          </div>
                          <div
                            className={`absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full border-2 border-slate-900 ${statusColors[account.status]}`}
                          />
                        </div>
                        <div>
                          <h3 className="font-semibold text-white">
                            {account.firstName} {account.lastName}
                          </h3>
                          <p className="text-sm text-sky-400">
                            {account.username ? `@${account.username}` : 'No username'}
                          </p>
                        </div>
                      </div>

                      <button
                        onClick={() =>
                          setExpandedId(expandedId === account.id ? null : account.id)
                        }
                        className="p-2 rounded-lg hover:bg-white/5 text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
                      >
                        <ChevronDown
                          size={16}
                          className={`transition-transform duration-300 ${
                            expandedId === account.id ? 'rotate-180' : ''
                          }`}
                        />
                      </button>
                    </div>

                    {/* Quick info */}
                    <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        <Phone size={12} />
                        {account.phone}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock size={12} />
                        {new Date(account.loginDate).toLocaleDateString()}
                      </span>
                      {account.appName && (
                        <span className="flex items-center gap-1 text-purple-400">
                          <Globe size={12} />
                          {account.appName}
                        </span>
                      )}
                    </div>
                    {account.deviceModel && (
                      <div className="mt-2 text-xs text-slate-600">
                        📱 {account.deviceModel}
                      </div>
                    )}
                  </div>

                  {/* Expanded details */}
                  <AnimatePresence>
                    {expandedId === account.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                      >
                        <div className="px-5 pb-5 space-y-3 border-t border-white/5 pt-4">
                          {/* Details */}
                          {[
                            { label: 'API ID', value: account.apiId, icon: Hash, copyable: true },
                            {
                              label: 'API Hash',
                              value: account.apiHash.slice(0, 8) + '...',
                              fullValue: account.apiHash,
                              icon: Settings,
                              copyable: true,
                            },
                            {
                              label: 'Login Date',
                              value: formatDate(account.loginDate),
                              icon: Clock,
                            },
                            {
                              label: 'Status',
                              value:
                                account.status.charAt(0).toUpperCase() + account.status.slice(1),
                              icon: account.status === 'online' ? Wifi : WifiOff,
                            },
                          ].map((item) => (
                            <div
                              key={item.label}
                              className="flex items-center justify-between py-2 px-3 bg-white/[0.02] rounded-lg"
                            >
                              <div className="flex items-center gap-2 text-sm text-slate-400">
                                <item.icon size={14} />
                                {item.label}
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-sm text-white font-mono">{item.value}</span>
                                {item.copyable && (
                                  <button
                                    onClick={() =>
                                      handleCopy(
                                        'fullValue' in item && item.fullValue
                                          ? item.fullValue
                                          : item.value,
                                        `${account.id}-${item.label}`
                                      )
                                    }
                                    className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-white transition-colors cursor-pointer"
                                  >
                                    {copiedField === `${account.id}-${item.label}` ? (
                                      <Check size={12} className="text-emerald-400" />
                                    ) : (
                                      <Copy size={12} />
                                    )}
                                  </button>
                                )}
                              </div>
                            </div>
                          ))}

                          {/* Actions */}
                          <div className="flex gap-2 pt-2">
                            <GlowButton
                              onClick={() => handleDelete(account.id)}
                              variant={deleteConfirm === account.id ? 'danger' : 'ghost'}
                              disabled={deletingId === account.id}
                              className="flex-1"
                            >
                              {deletingId === account.id ? (
                                <RefreshCw size={14} className="animate-spin" />
                              ) : deleteConfirm === account.id ? (
                                <>
                                  <Trash2 size={14} />
                                  Confirm Delete
                                </>
                              ) : (
                                <>
                                  <LogOut size={14} />
                                  Remove
                                </>
                              )}
                            </GlowButton>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}
