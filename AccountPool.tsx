import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  ArrowLeft,
  RefreshCw,
  Zap,
  Coffee,
  AlertTriangle,
  Heart,
  Clock,
  Snowflake,
  Sun,
  Ban,
  Target,
} from 'lucide-react';

interface AccountPoolProps {
  onBack: () => void;
}

interface PoolAccount {
  account_id: string;
  phone: string;
  first_name: string;
  tier: string;
  state: string;
  is_available: boolean;
  age_days: number;
  sessions: number;
  targets_reported: number;
  health: {
    score: number;
    total_reports: number;
    successful: number;
    failed: number;
    success_rate: number;
    flood_waits: number;
    current_streak: number;
    hours_since_use: number;
  };
  cooldown: {
    active: boolean;
    reason: string | null;
    remaining_seconds: number;
  };
}

interface PoolStats {
  total: number;
  available: number;
  cooling: number;
  resting: number;
  working: number;
  banned: number;
  tiers: Record<string, number>;
  avg_health: number;
  critical_count: number;
  healthy_count: number;
}

interface Recommendation {
  type: string;
  severity: string;
  message: string;
  accounts?: string[];
}

export default function AccountPool({ onBack }: AccountPoolProps) {
  const [loading, setLoading] = useState(true);
  const [accounts, setAccounts] = useState<PoolAccount[]>([]);
  const [stats, setStats] = useState<PoolStats | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/pool');
      const data = await res.json();
      if (data.success) {
        setAccounts(data.accounts || []);
        setStats(data.stats);
        setRecommendations(data.recommendations || []);
      }
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleRest = async (accountId: string) => {
    await fetch('http://localhost:8000/api/pool/rest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account_id: accountId, hours: 6 }),
    });
    await fetchData();
  };

  const handleWake = async (accountId: string) => {
    await fetch(`http://localhost:8000/api/pool/wake/${accountId}`, { method: 'POST' });
    await fetchData();
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'elite': return 'text-amber-400 bg-amber-500/10';
      case 'veteran': return 'text-purple-400 bg-purple-500/10';
      case 'regular': return 'text-sky-400 bg-sky-500/10';
      case 'rookie': return 'text-emerald-400 bg-emerald-500/10';
      default: return 'text-slate-400 bg-slate-500/10';
    }
  };

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'elite': return '👑';
      case 'veteran': return '⭐';
      case 'regular': return '🔵';
      case 'rookie': return '🟢';
      default: return '⚪';
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'available': return <Sun size={14} className="text-emerald-400" />;
      case 'cooling': return <Snowflake size={14} className="text-sky-400" />;
      case 'resting': return <Coffee size={14} className="text-amber-400" />;
      case 'working': return <Zap size={14} className="text-purple-400" />;
      case 'banned': return <Ban size={14} className="text-red-400" />;
      default: return <AlertTriangle size={14} className="text-slate-400" />;
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 70) return 'bg-emerald-500';
    if (score >= 40) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const getHealthTextColor = (score: number) => {
    if (score >= 70) return 'text-emerald-400';
    if (score >= 40) return 'text-amber-400';
    return 'text-red-400';
  };

  if (loading && !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RefreshCw size={32} className="text-sky-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div className="flex items-center gap-4">
            <button onClick={onBack} className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all cursor-pointer">
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-3">
                <Users className="text-emerald-400" />
                Account Pool
              </h1>
              <p className="text-sm text-slate-400">Smart rotation & health monitoring</p>
            </div>
          </div>
          <button onClick={fetchData} className="p-2.5 bg-white/5 border border-white/10 rounded-xl text-slate-400 hover:text-white transition-all cursor-pointer">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </motion.div>

        {/* Stats */}
        {stats && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6">
            {[
              { label: 'Total', value: stats.total, icon: Users, color: 'sky' },
              { label: 'Available', value: stats.available, icon: Sun, color: 'emerald' },
              { label: 'Cooling', value: stats.cooling, icon: Snowflake, color: 'blue' },
              { label: 'Resting', value: stats.resting, icon: Coffee, color: 'amber' },
              { label: 'Avg Health', value: `${stats.avg_health}`, icon: Heart, color: stats.avg_health >= 70 ? 'emerald' : stats.avg_health >= 40 ? 'amber' : 'red' },
              { label: 'Critical', value: stats.critical_count, icon: AlertTriangle, color: 'red' },
            ].map((s) => (
              <div key={s.label} className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-3 text-center">
                <div className={`inline-flex items-center justify-center w-8 h-8 rounded-lg mb-1 ${
                  s.color === 'emerald' ? 'bg-emerald-500/10 text-emerald-400' :
                  s.color === 'amber' ? 'bg-amber-500/10 text-amber-400' :
                  s.color === 'red' ? 'bg-red-500/10 text-red-400' :
                  s.color === 'blue' ? 'bg-blue-500/10 text-blue-400' :
                  'bg-sky-500/10 text-sky-400'
                }`}>
                  <s.icon size={16} />
                </div>
                <p className="text-xl font-bold text-white">{s.value}</p>
                <p className="text-[10px] text-slate-500">{s.label}</p>
              </div>
            ))}
          </motion.div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="mb-6 space-y-2">
            {recommendations.map((rec, i) => (
              <div key={i} className={`p-3 rounded-xl flex items-start gap-3 ${
                rec.severity === 'high' ? 'bg-red-500/10 border border-red-500/20' : 'bg-amber-500/10 border border-amber-500/20'
              }`}>
                <AlertTriangle size={16} className={rec.severity === 'high' ? 'text-red-400 mt-0.5' : 'text-amber-400 mt-0.5'} />
                <div>
                  <p className={`text-sm ${rec.severity === 'high' ? 'text-red-300' : 'text-amber-300'}`}>{rec.message}</p>
                  {rec.accounts && (
                    <p className="text-xs text-slate-500 mt-1">{rec.accounts.join(', ')}</p>
                  )}
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* Account Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          <AnimatePresence>
            {accounts.map((account, index) => (
              <motion.div
                key={account.account_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className={`bg-slate-900/60 backdrop-blur-xl border rounded-2xl p-5 ${
                  account.state === 'banned' ? 'border-red-500/30 opacity-60' :
                  account.state === 'resting' ? 'border-amber-500/20' :
                  account.health.score < 30 ? 'border-red-500/20' :
                  'border-white/5'
                }`}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-sky-400 to-blue-600 flex items-center justify-center text-white font-bold shadow-lg">
                      {account.first_name?.[0] || '?'}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">{account.first_name || 'Unknown'}</p>
                      <p className="text-xs text-slate-500">{account.phone}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getTierColor(account.tier)}`}>
                      {getTierIcon(account.tier)} {account.tier.toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Health Bar */}
                <div className="mb-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Heart size={10} /> Health
                    </span>
                    <span className={`text-xs font-bold ${getHealthTextColor(account.health.score)}`}>
                      {Math.round(account.health.score)}%
                    </span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className={`h-full transition-all duration-500 ${getHealthColor(account.health.score)}`} style={{ width: `${account.health.score}%` }} />
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <div className="text-center p-1.5 bg-white/5 rounded-lg">
                    <p className="text-xs text-emerald-400 font-bold">{account.health.successful}</p>
                    <p className="text-[10px] text-slate-500">Success</p>
                  </div>
                  <div className="text-center p-1.5 bg-white/5 rounded-lg">
                    <p className="text-xs text-red-400 font-bold">{account.health.failed}</p>
                    <p className="text-[10px] text-slate-500">Failed</p>
                  </div>
                  <div className="text-center p-1.5 bg-white/5 rounded-lg">
                    <p className="text-xs text-amber-400 font-bold">{account.health.flood_waits}</p>
                    <p className="text-[10px] text-slate-500">Floods</p>
                  </div>
                </div>

                {/* Status & Info */}
                <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
                  <span className="flex items-center gap-1">
                    {getStateIcon(account.state)}
                    <span className="capitalize">{account.state}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock size={10} />
                    {account.health.hours_since_use < 1 
                      ? `${Math.round(account.health.hours_since_use * 60)}m ago`
                      : account.health.hours_since_use < 24
                        ? `${Math.round(account.health.hours_since_use)}h ago`
                        : `${Math.round(account.health.hours_since_use / 24)}d ago`
                    }
                  </span>
                  <span className="flex items-center gap-1">
                    <Target size={10} />
                    {account.targets_reported}
                  </span>
                </div>

                {/* Cooldown indicator */}
                {account.cooldown.active && (
                  <div className="p-2 bg-sky-500/10 rounded-lg mb-3 flex items-center gap-2">
                    <Snowflake size={12} className="text-sky-400" />
                    <span className="text-xs text-sky-300">
                      Cooling: {Math.round(account.cooldown.remaining_seconds)}s 
                      {account.cooldown.reason && ` (${account.cooldown.reason.replace('_', ' ')})`}
                    </span>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  {account.state === 'resting' ? (
                    <button onClick={() => handleWake(account.account_id)} className="flex-1 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-xs hover:bg-emerald-500/20 transition-all cursor-pointer flex items-center justify-center gap-1">
                      <Sun size={12} /> Wake Up
                    </button>
                  ) : account.state !== 'banned' && (
                    <button onClick={() => handleRest(account.account_id)} className="flex-1 py-2 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400 text-xs hover:bg-amber-500/20 transition-all cursor-pointer flex items-center justify-center gap-1">
                      <Coffee size={12} /> Rest 6h
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {accounts.length === 0 && (
          <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-3xl p-12 text-center">
            <Users size={40} className="text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">No Accounts in Pool</h3>
            <p className="text-sm text-slate-400">Login accounts first, they'll automatically appear here.</p>
          </div>
        )}
      </div>
    </div>
  );
}
