import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Globe,
  Plus,
  Trash2,
  RefreshCw,
  Check,
  X,
  Upload,
  Zap,
  Shield,
  Clock,
  MapPin,
  ArrowLeft,
  AlertTriangle,
  Loader2,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { api, ProxyInfo, ProxyStats } from '../api';
import GlowButton from './GlowButton';

interface ProxyManagerProps {
  onBack: () => void;
}

export default function ProxyManager({ onBack }: ProxyManagerProps) {
  const [proxies, setProxies] = useState<ProxyInfo[]>([]);
  const [stats, setStats] = useState<ProxyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [importText, setImportText] = useState('');
  const [showImport, setShowImport] = useState(false);
  const [validateOnImport, setValidateOnImport] = useState(true);
  const [importResult, setImportResult] = useState<{
    added: number;
    failed: number;
    duplicates: number;
  } | null>(null);

  const fetchProxies = async () => {
    setLoading(true);
    const result = await api.getProxies();
    if (result.success) {
      setProxies(result.proxies);
      setStats(result.stats);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchProxies();
  }, []);

  const handleImport = async () => {
    const lines = importText
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (lines.length === 0) return;

    setImporting(true);
    setImportResult(null);

    const result = await api.addProxies(lines, validateOnImport);

    setImportResult({
      added: result.added,
      failed: result.failed,
      duplicates: result.duplicates,
    });

    if (result.stats) {
      setStats(result.stats);
    }

    setImporting(false);
    setImportText('');
    await fetchProxies();
  };

  const handleRemoveUsed = async () => {
    await api.removeUsedProxies();
    await fetchProxies();
  };

  const handleRemoveDead = async () => {
    await api.removeDeadProxies();
    await fetchProxies();
  };

  const handleClearAll = async () => {
    if (confirm('Are you sure you want to remove ALL proxies?')) {
      await api.clearAllProxies();
      await fetchProxies();
    }
  };

  const getProxyTypeColor = (type: string) => {
    switch (type) {
      case 'socks5':
        return 'text-sky-400 bg-sky-500/10';
      case 'socks4':
        return 'text-blue-400 bg-blue-500/10';
      case 'http':
      case 'https':
        return 'text-emerald-400 bg-emerald-500/10';
      case 'mtproto':
        return 'text-purple-400 bg-purple-500/10';
      default:
        return 'text-slate-400 bg-slate-500/10';
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8"
        >
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all cursor-pointer"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-3">
                <Globe className="text-purple-400" />
                Proxy Manager
              </h1>
              <p className="text-sm text-slate-400">
                One-time use proxies with auto-rotation
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchProxies}
              className="p-2.5 bg-white/5 border border-white/10 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-all cursor-pointer"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
            <GlowButton onClick={() => setShowImport(!showImport)}>
              <Plus size={18} />
              Import Proxies
            </GlowButton>
          </div>
        </motion.div>

        {/* Stats Cards */}
        {stats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8"
          >
            {[
              { label: 'Total', value: stats.total, icon: Globe, color: 'sky' },
              { label: 'Available', value: stats.available, icon: Zap, color: 'emerald' },
              { label: 'Used', value: stats.used, icon: Check, color: 'amber' },
              { label: 'Dead', value: stats.dead, icon: X, color: 'red' },
              { label: 'Validated', value: stats.validated, icon: Shield, color: 'purple' },
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
                          : stat.color === 'red'
                            ? 'bg-red-500/10 text-red-400'
                            : 'bg-purple-500/10 text-purple-400'
                  }`}
                >
                  <stat.icon size={18} />
                </div>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
                <p className="text-xs text-slate-500">{stat.label}</p>
              </div>
            ))}
          </motion.div>
        )}

        {/* Import Section */}
        <AnimatePresence>
          {showImport && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-8 overflow-hidden"
            >
              <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Upload size={18} className="text-purple-400" />
                  Import Proxies
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-slate-400 mb-2 block">
                      Paste proxies (one per line)
                    </label>
                    <textarea
                      value={importText}
                      onChange={(e) => setImportText(e.target.value)}
                      placeholder={`Supported formats:
host:port
host:port:username:password
socks5://host:port
socks5://user:pass@host:port
http://host:port
mtproto://host:port`}
                      className="w-full h-40 px-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white placeholder-slate-600 font-mono text-sm focus:outline-none focus:border-purple-500/50 resize-none"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={validateOnImport}
                        onChange={(e) => setValidateOnImport(e.target.checked)}
                        className="w-4 h-4 rounded border-white/20 bg-white/5 text-purple-500 focus:ring-purple-500/20"
                      />
                      <span className="text-sm text-slate-400">
                        Validate proxies before adding (slower but recommended)
                      </span>
                    </label>

                    <GlowButton onClick={handleImport} disabled={importing || !importText.trim()}>
                      {importing ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          Importing...
                        </>
                      ) : (
                        <>
                          <Upload size={16} />
                          Import
                        </>
                      )}
                    </GlowButton>
                  </div>

                  {/* Import Result */}
                  {importResult && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-center gap-4 p-4 bg-white/5 rounded-xl"
                    >
                      <div className="flex items-center gap-2 text-emerald-400">
                        <CheckCircle2 size={16} />
                        <span className="text-sm">{importResult.added} added</span>
                      </div>
                      <div className="flex items-center gap-2 text-red-400">
                        <XCircle size={16} />
                        <span className="text-sm">{importResult.failed} failed</span>
                      </div>
                      <div className="flex items-center gap-2 text-amber-400">
                        <AlertTriangle size={16} />
                        <span className="text-sm">{importResult.duplicates} duplicates</span>
                      </div>
                    </motion.div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-wrap gap-3 mb-6"
        >
          <button
            onClick={handleRemoveUsed}
            className="px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-400 text-sm hover:bg-amber-500/20 transition-all cursor-pointer flex items-center gap-2"
          >
            <Trash2 size={14} />
            Remove Used
          </button>
          <button
            onClick={handleRemoveDead}
            className="px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm hover:bg-red-500/20 transition-all cursor-pointer flex items-center gap-2"
          >
            <X size={14} />
            Remove Dead
          </button>
          <button
            onClick={handleClearAll}
            className="px-4 py-2 bg-slate-500/10 border border-slate-500/20 rounded-xl text-slate-400 text-sm hover:bg-slate-500/20 transition-all cursor-pointer flex items-center gap-2"
          >
            <Trash2 size={14} />
            Clear All
          </button>
        </motion.div>

        {/* Proxy List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw size={32} className="text-purple-400 animate-spin" />
          </div>
        ) : proxies.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-3xl p-12 text-center"
          >
            <div className="w-20 h-20 rounded-full bg-purple-500/10 flex items-center justify-center mx-auto mb-6">
              <Globe size={40} className="text-purple-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No Proxies</h3>
            <p className="text-sm text-slate-400 mb-6 max-w-sm mx-auto">
              Import proxies to enable automatic rotation during login. Each proxy is used only
              once.
            </p>
            <GlowButton onClick={() => setShowImport(true)}>
              <Plus size={18} />
              Import Proxies
            </GlowButton>
          </motion.div>
        ) : (
          <div className="grid gap-3">
            {proxies.map((proxy, index) => (
              <motion.div
                key={proxy.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.02 }}
                className={`bg-slate-900/60 backdrop-blur-xl border rounded-xl p-4 ${
                  proxy.used
                    ? 'border-amber-500/20 opacity-60'
                    : proxy.validated
                      ? 'border-emerald-500/20'
                      : 'border-white/5'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {/* Status indicator */}
                    <div
                      className={`w-3 h-3 rounded-full ${
                        proxy.used
                          ? 'bg-amber-500'
                          : proxy.validated
                            ? 'bg-emerald-500'
                            : 'bg-slate-500'
                      }`}
                    />

                    {/* Proxy info */}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-white">
                          {proxy.host}:{proxy.port}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium ${getProxyTypeColor(proxy.type)}`}
                        >
                          {proxy.type.toUpperCase()}
                        </span>
                        {proxy.used && (
                          <span className="px-2 py-0.5 rounded text-xs font-medium text-amber-400 bg-amber-500/10">
                            USED
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
                        {proxy.latency_ms && (
                          <span className="flex items-center gap-1">
                            <Clock size={10} />
                            {proxy.latency_ms}ms
                          </span>
                        )}
                        {proxy.country && (
                          <span className="flex items-center gap-1">
                            <MapPin size={10} />
                            {proxy.country}{proxy.city ? `, ${proxy.city}` : ''}
                          </span>
                        )}
                        {proxy.isp && (
                          <span className="text-slate-600 truncate max-w-[150px]">{proxy.isp}</span>
                        )}
                        {proxy.quality && proxy.quality !== 'unknown' && (
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            proxy.quality === 'residential' ? 'text-emerald-400 bg-emerald-500/10' :
                            proxy.quality === 'mobile' ? 'text-sky-400 bg-sky-500/10' :
                            proxy.quality === 'isp' ? 'text-blue-400 bg-blue-500/10' :
                            'text-amber-400 bg-amber-500/10'
                          }`}>
                            {proxy.quality.toUpperCase()}
                          </span>
                        )}
                        {proxy.quality_score !== undefined && proxy.quality_score > 0 && (
                          <span className={`text-[10px] font-mono ${
                            proxy.quality_score >= 80 ? 'text-emerald-400' :
                            proxy.quality_score >= 50 ? 'text-amber-400' :
                            'text-red-400'
                          }`}>
                            Q:{Math.round(proxy.quality_score)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Validation status */}
                  <div className="flex items-center gap-2">
                    {proxy.validated ? (
                      <span className="flex items-center gap-1 text-xs text-emerald-400">
                        <Check size={14} />
                        Valid
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-slate-500">
                        <Clock size={14} />
                        Pending
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
