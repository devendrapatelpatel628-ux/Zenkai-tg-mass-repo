import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Flag,
  ArrowLeft,
  Plus,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Target,
  Loader2,
  History,
  BarChart3,
  Send,
  Zap,
  MessageSquare,
  Shuffle,
  Coffee,
  Clock,
  SkipForward,
} from 'lucide-react';
import { api } from '../api';
import GlowButton from './GlowButton';

interface ReportManagerProps {
  onBack: () => void;
}

interface ReportReason {
  id: string;
  name: string;
  description: string;
}

interface Account {
  id: string;
  phone: string;
  firstName: string;
  status: string;
}

interface ReportSession {
  id: string;
  status: string;
  targets: string[];
  reason: string;
  successful_reports: number;
  failed_reports: number;
  skipped_reports?: number;
  total_reports: number;
  created_at: string;
}

interface ReportStats {
  total_sessions: number;
  total_reports: number;
  successful_reports: number;
  failed_reports: number;
  skipped_reports?: number;
  success_rate: number;
  today_reports: number;
  active_sessions: number;
}

const MAX_DESCRIPTION_LENGTH = 4000;

export default function ReportManager({ onBack }: ReportManagerProps) {
  const [view, setView] = useState<'main' | 'new' | 'history'>('main');
  const [loading, setLoading] = useState(true);
  const [reasons, setReasons] = useState<ReportReason[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [sessions, setSessions] = useState<ReportSession[]>([]);
  const [stats, setStats] = useState<ReportStats | null>(null);
  
  // New report form
  const [targets, setTargets] = useState('');
  const [selectedReason, setSelectedReason] = useState('spam');
  const [reportDescription, setReportDescription] = useState('');
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [delayMin, setDelayMin] = useState(3);
  const [delayMax, setDelayMax] = useState(10);
  const [humanizeEnabled, setHumanizeEnabled] = useState(true);
  const [stealthLevel, setStealthLevel] = useState<'normal' | 'stealth' | 'paranoid'>('stealth');
  const [collectEvidence, setCollectEvidence] = useState(false);
  const [useSmartPool, setUseSmartPool] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<{ success: boolean; message: string } | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    
    try {
      // Fetch reasons
      const reasonsRes = await fetch('http://localhost:8000/api/reports/reasons');
      const reasonsData = await reasonsRes.json();
      setReasons(reasonsData.reasons || []);
      
      // Fetch accounts
      const accountsRes = await api.getAccounts();
      if (accountsRes.success) {
        setAccounts(accountsRes.accounts.map(a => ({
          id: a.id,
          phone: a.phone,
          firstName: a.firstName,
          status: a.status,
        })));
      }
      
      // Fetch sessions
      const sessionsRes = await fetch('http://localhost:8000/api/reports/sessions');
      const sessionsData = await sessionsRes.json();
      setSessions(sessionsData.sessions || []);
      
      // Fetch stats
      const statsRes = await fetch('http://localhost:8000/api/reports/stats');
      const statsData = await statsRes.json();
      setStats(statsData.stats);
      
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
    
    // Poll for updates
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleSelectAllAccounts = () => {
    if (selectedAccounts.length === accounts.length) {
      setSelectedAccounts([]);
    } else {
      setSelectedAccounts(accounts.map(a => a.id));
    }
  };

  const handleToggleAccount = (id: string) => {
    setSelectedAccounts(prev =>
      prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]
    );
  };

  const handleStartReport = async () => {
    const targetList = targets
      .split('\n')
      .map(t => t.trim())
      .filter(t => t.length > 0);
    
    if (targetList.length === 0) {
      setSubmitResult({ success: false, message: 'Please enter at least one target' });
      return;
    }
    
    if (selectedAccounts.length === 0) {
      setSubmitResult({ success: false, message: 'Please select at least one account' });
      return;
    }
    
    setSubmitting(true);
    setSubmitResult(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/reports/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          targets: targetList,
          reason: selectedReason,
          message: reportDescription,
          account_ids: selectedAccounts,
          delay_min: delayMin,
          delay_max: delayMax,
          humanize: humanizeEnabled,
          stealth_level: stealthLevel,
          collect_evidence: collectEvidence,
          use_smart_pool: useSmartPool,
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSubmitResult({
          success: true,
          message: `🚀 Report session started! ID: ${data.data.session_id}`,
        });
        setTargets('');
        setReportDescription('');
        setTimeout(() => {
          setView('main');
          fetchData();
        }, 2000);
      } else {
        setSubmitResult({ success: false, message: data.error || 'Failed to start report' });
      }
    } catch (error) {
      setSubmitResult({ success: false, message: 'Network error - is the backend running?' });
    }
    
    setSubmitting(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-emerald-400 bg-emerald-500/10';
      case 'in_progress': return 'text-amber-400 bg-amber-500/10';
      case 'failed': return 'text-red-400 bg-red-500/10';
      default: return 'text-slate-400 bg-slate-500/10';
    }
  };

  const getReasonIcon = (reason: string) => {
    switch (reason) {
      case 'spam': return '🚫';
      case 'violence': return '⚠️';
      case 'fake': return '🎭';
      case 'scam': return '💰';
      case 'pornography': return '🔞';
      case 'child_abuse': return '🛡️';
      case 'illegal_drugs': return '💊';
      case 'copyright': return '©️';
      default: return '📋';
    }
  };

  const descriptionLength = reportDescription.length;
  const descriptionPercentage = (descriptionLength / MAX_DESCRIPTION_LENGTH) * 100;

  if (loading && !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RefreshCw size={32} className="text-red-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-red-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-orange-500/5 rounded-full blur-3xl" />
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
                <Flag className="text-red-400" />
                Report Manager
              </h1>
              <p className="text-sm text-slate-400">
                Human-like mass reporting system
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchData}
              className="p-2.5 bg-white/5 border border-white/10 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-all cursor-pointer"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
            
            <button
              onClick={() => setView('history')}
              className={`p-2.5 rounded-xl transition-all cursor-pointer flex items-center gap-2 ${
                view === 'history'
                  ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                  : 'bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10'
              }`}
            >
              <History size={16} />
            </button>
            
            <GlowButton onClick={() => setView('new')} variant="danger">
              <Plus size={18} />
              New Report
            </GlowButton>
          </div>
        </motion.div>

        {/* Stats Cards */}
        {stats && view === 'main' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8"
          >
            {[
              { label: 'Total Reports', value: stats.total_reports, icon: Flag, color: 'red' },
              { label: 'Successful', value: stats.successful_reports, icon: CheckCircle2, color: 'emerald' },
              { label: 'Failed', value: stats.failed_reports, icon: XCircle, color: 'amber' },
              { label: 'Skipped', value: stats.skipped_reports || 0, icon: SkipForward, color: 'slate' },
              { label: 'Success Rate', value: `${stats.success_rate}%`, icon: BarChart3, color: 'sky' },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-4 text-center"
              >
                <div
                  className={`inline-flex items-center justify-center w-10 h-10 rounded-xl mb-2 ${
                    stat.color === 'red'
                      ? 'bg-red-500/10 text-red-400'
                      : stat.color === 'emerald'
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : stat.color === 'amber'
                          ? 'bg-amber-500/10 text-amber-400'
                          : stat.color === 'slate'
                            ? 'bg-slate-500/10 text-slate-400'
                            : 'bg-sky-500/10 text-sky-400'
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

        {/* Main View - Recent Sessions */}
        {view === 'main' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Zap className="text-amber-400" />
              Recent Sessions
            </h2>
            
            {sessions.length === 0 ? (
              <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-12 text-center">
                <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
                  <Flag size={32} className="text-red-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">No Report Sessions</h3>
                <p className="text-sm text-slate-400 mb-6">
                  Start a new reporting session to see activity here
                </p>
                <GlowButton onClick={() => setView('new')} variant="danger">
                  <Plus size={18} />
                  Start First Report
                </GlowButton>
              </div>
            ) : (
              <div className="space-y-3">
                {sessions.slice(0, 10).map((session, index) => (
                  <motion.div
                    key={session.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="text-2xl">{getReasonIcon(session.reason)}</div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-white">Session #{session.id}</span>
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(session.status)}`}>
                              {session.status.toUpperCase()}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
                            <span className="flex items-center gap-1">
                              <Target size={12} />
                              {Array.isArray(session.targets) ? session.targets.length : 0} targets
                            </span>
                            <span className="flex items-center gap-1">
                              <Flag size={12} />
                              {session.reason}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-emerald-400">{session.successful_reports} ✓</span>
                            <span className="text-red-400">{session.failed_reports} ✗</span>
                            {(session.skipped_reports || 0) > 0 && (
                              <span className="text-slate-400">{session.skipped_reports} ⏭</span>
                            )}
                          </div>
                          <p className="text-xs text-slate-500">
                            {new Date(session.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* New Report Form */}
        <AnimatePresence>
          {view === 'new' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Send className="text-red-400" />
                  New Report Session
                </h2>
                <button
                  onClick={() => setView('main')}
                  className="text-sm text-slate-400 hover:text-white cursor-pointer"
                >
                  Cancel
                </button>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {/* Left Column - Targets & Description */}
                <div className="space-y-4">
                  <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
                    <label className="text-sm font-medium text-slate-300 mb-2 block">
                      Targets (one per line)
                    </label>
                    <textarea
                      value={targets}
                      onChange={(e) => setTargets(e.target.value)}
                      placeholder={`@username1
@spammer_account  
t.me/bad_channel
user_id_123456`}
                      className="w-full h-32 px-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white placeholder-slate-600 font-mono text-sm focus:outline-none focus:border-red-500/50 resize-none"
                    />
                    <p className="text-xs text-slate-500 mt-2">
                      {targets.split('\n').filter(t => t.trim()).length} targets entered
                    </p>
                  </div>

                  {/* Report Description - NEW */}
                  <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-slate-300 flex items-center gap-2">
                        <MessageSquare size={14} className="text-red-400" />
                        Report Description
                      </label>
                      <span className={`text-xs ${
                        descriptionLength > MAX_DESCRIPTION_LENGTH * 0.9 
                          ? 'text-red-400' 
                          : descriptionLength > MAX_DESCRIPTION_LENGTH * 0.7 
                            ? 'text-amber-400' 
                            : 'text-slate-500'
                      }`}>
                        {descriptionLength.toLocaleString()} / {MAX_DESCRIPTION_LENGTH.toLocaleString()}
                      </span>
                    </div>
                    <textarea
                      value={reportDescription}
                      onChange={(e) => {
                        if (e.target.value.length <= MAX_DESCRIPTION_LENGTH) {
                          setReportDescription(e.target.value);
                        }
                      }}
                      placeholder="Describe why you're reporting this account...

Example: This account has been sending me spam messages daily for the past week. They're promoting fake cryptocurrency investments and trying to scam people out of their money. I've blocked them multiple times but they keep creating new accounts."
                      className="w-full h-40 px-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white placeholder-slate-600 text-sm focus:outline-none focus:border-red-500/50 resize-none"
                    />
                    {/* Character progress bar */}
                    <div className="mt-2 h-1 bg-white/5 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-300 ${
                          descriptionPercentage > 90 
                            ? 'bg-red-500' 
                            : descriptionPercentage > 70 
                              ? 'bg-amber-500' 
                              : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(descriptionPercentage, 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-2">
                      💡 Write naturally - the system adds variations automatically
                    </p>
                  </div>

                  <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
                    <label className="text-sm font-medium text-slate-300 mb-3 block">
                      Report Reason
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {reasons.map((reason) => (
                        <button
                          key={reason.id}
                          onClick={() => setSelectedReason(reason.id)}
                          className={`p-3 rounded-xl text-left transition-all cursor-pointer ${
                            selectedReason === reason.id
                              ? 'bg-red-500/20 border border-red-500/30 text-red-400'
                              : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10'
                          }`}
                        >
                          <span className="text-lg mr-2">{getReasonIcon(reason.id)}</span>
                          <span className="text-sm font-medium">{reason.name}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Column - Accounts & Settings */}
                <div className="space-y-4">
                  <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-3">
                      <label className="text-sm font-medium text-slate-300">
                        Select Accounts
                      </label>
                      <button
                        onClick={handleSelectAllAccounts}
                        className="text-xs text-red-400 hover:text-red-300 cursor-pointer"
                      >
                        {selectedAccounts.length === accounts.length ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {accounts.map((account) => (
                        <label
                          key={account.id}
                          className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                            selectedAccounts.includes(account.id)
                              ? 'bg-red-500/10 border border-red-500/30'
                              : 'bg-white/5 border border-white/10 hover:bg-white/10'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={selectedAccounts.includes(account.id)}
                            onChange={() => handleToggleAccount(account.id)}
                            className="w-4 h-4 rounded border-white/20 bg-white/5 text-red-500 focus:ring-red-500/20"
                          />
                          <div className="flex-1">
                            <p className="text-sm text-white">{account.firstName}</p>
                            <p className="text-xs text-slate-500">{account.phone}</p>
                          </div>
                          <span className={`w-2 h-2 rounded-full ${
                            account.status === 'online' ? 'bg-emerald-500' : 'bg-slate-500'
                          }`} />
                        </label>
                      ))}
                      {accounts.length === 0 && (
                        <p className="text-sm text-slate-500 text-center py-4">
                          No accounts available. Add accounts first.
                        </p>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-2">
                      {selectedAccounts.length} accounts selected
                    </p>
                  </div>

                  {/* Human-like Settings */}
                  <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
                    <label className="text-sm font-medium text-slate-300 mb-4 block flex items-center gap-2">
                      <Shuffle size={14} className="text-purple-400" />
                      Human-like Behavior
                    </label>
                    
                    <label className="flex items-center gap-3 p-3 rounded-xl bg-white/5 cursor-pointer mb-4">
                      <input
                        type="checkbox"
                        checked={humanizeEnabled}
                        onChange={(e) => setHumanizeEnabled(e.target.checked)}
                        className="w-4 h-4 rounded border-white/20 bg-white/5 text-purple-500 focus:ring-purple-500/20"
                      />
                      <div>
                        <p className="text-sm text-white">Enable Humanizer</p>
                        <p className="text-xs text-slate-500">Random delays, message variations, natural patterns</p>
                      </div>
                    </label>

                    {humanizeEnabled && (
                      <div className="space-y-2 text-xs text-slate-500 pl-2 border-l-2 border-purple-500/30 mb-4">
                        <p className="flex items-center gap-2">
                          <Shuffle size={12} className="text-purple-400" />
                          Shuffled target & account order
                        </p>
                        <p className="flex items-center gap-2">
                          <MessageSquare size={12} className="text-purple-400" />
                          Message variations for each report
                        </p>
                        <p className="flex items-center gap-2">
                          <Coffee size={12} className="text-purple-400" />
                          Natural breaks & fatigue simulation
                        </p>
                        <p className="flex items-center gap-2">
                          <SkipForward size={12} className="text-purple-400" />
                          Occasional natural skips (~2%)
                        </p>
                      </div>
                    )}
                    
                    {/* Stealth Level Selector */}
                    <div className="mt-4">
                      <p className="text-xs text-slate-400 mb-2">🛡️ Stealth Level</p>
                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { id: 'normal' as const, label: 'Normal', desc: 'Basic protection', color: 'emerald' },
                          { id: 'stealth' as const, label: 'Stealth', desc: 'Enhanced anti-detection', color: 'amber' },
                          { id: 'paranoid' as const, label: 'Paranoid', desc: 'Maximum protection', color: 'red' },
                        ].map((level) => (
                          <button
                            key={level.id}
                            onClick={() => setStealthLevel(level.id)}
                            className={`p-2.5 rounded-xl text-center transition-all cursor-pointer ${
                              stealthLevel === level.id
                                ? level.color === 'emerald'
                                  ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400'
                                  : level.color === 'amber'
                                    ? 'bg-amber-500/20 border border-amber-500/30 text-amber-400'
                                    : 'bg-red-500/20 border border-red-500/30 text-red-400'
                                : 'bg-white/5 border border-white/10 text-slate-500 hover:bg-white/10'
                            }`}
                          >
                            <p className="text-xs font-bold">{level.label}</p>
                            <p className="text-[10px] opacity-70 mt-0.5">{level.desc}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                   {/* Integration Toggles */}
                   <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6 space-y-3">
                    <p className="text-sm font-medium text-slate-300 mb-1">⚡ Integrations</p>
                    
                    <label className="flex items-center justify-between p-3 bg-white/5 rounded-xl cursor-pointer">
                      <div>
                        <p className="text-sm text-white">🧠 Smart Account Pool</p>
                        <p className="text-[10px] text-slate-500">Auto-select best accounts by health & cooldown</p>
                      </div>
                      <input type="checkbox" checked={useSmartPool} onChange={(e) => setUseSmartPool(e.target.checked)} className="w-4 h-4 rounded accent-emerald-500" />
                    </label>
                    
                    <label className="flex items-center justify-between p-3 bg-white/5 rounded-xl cursor-pointer">
                      <div>
                        <p className="text-sm text-white">📸 Collect Evidence First</p>
                        <p className="text-[10px] text-slate-500">Screenshot profiles & messages before reporting</p>
                      </div>
                      <input type="checkbox" checked={collectEvidence} onChange={(e) => setCollectEvidence(e.target.checked)} className="w-4 h-4 rounded accent-amber-500" />
                    </label>
                   </div>

                   <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
                    <label className="text-sm font-medium text-slate-300 mb-3 block flex items-center gap-2">
                      <Clock size={14} className="text-amber-400" />
                      Delay Between Reports
                    </label>
                    <div className="flex items-center gap-4">
                      <div className="flex-1">
                        <label className="text-xs text-slate-500 mb-1 block">Min (sec)</label>
                        <input
                          type="number"
                          value={delayMin}
                          onChange={(e) => setDelayMin(Number(e.target.value))}
                          min={1}
                          max={30}
                          className="w-full px-3 py-2 bg-black/30 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-red-500/50"
                        />
                      </div>
                      <div className="text-slate-500 pt-4">—</div>
                      <div className="flex-1">
                        <label className="text-xs text-slate-500 mb-1 block">Max (sec)</label>
                        <input
                          type="number"
                          value={delayMax}
                          onChange={(e) => setDelayMax(Number(e.target.value))}
                          min={1}
                          max={120}
                          className="w-full px-3 py-2 bg-black/30 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-red-500/50"
                        />
                      </div>
                    </div>
                    <p className="text-xs text-slate-500 mt-2">
                      {humanizeEnabled 
                        ? '🎲 Delays will vary naturally based on time of day & fatigue'
                        : `Fixed random delay between ${delayMin}s and ${delayMax}s`
                      }
                    </p>
                  </div>

                  {/* Submit Result */}
                  {submitResult && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`p-4 rounded-xl flex items-center gap-3 ${
                        submitResult.success
                          ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                          : 'bg-red-500/10 border border-red-500/20 text-red-400'
                      }`}
                    >
                      {submitResult.success ? <CheckCircle2 size={20} /> : <XCircle size={20} />}
                      <span className="text-sm">{submitResult.message}</span>
                    </motion.div>
                  )}

                  <GlowButton
                    onClick={handleStartReport}
                    disabled={submitting || selectedAccounts.length === 0}
                    variant="danger"
                    className="w-full"
                  >
                    {submitting ? (
                      <>
                        <Loader2 size={18} className="animate-spin" />
                        Starting...
                      </>
                    ) : (
                      <>
                        <Flag size={18} />
                        Start Report ({targets.split('\n').filter(t => t.trim()).length} × {selectedAccounts.length})
                      </>
                    )}
                  </GlowButton>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* History View */}
        <AnimatePresence>
          {view === 'history' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <History className="text-red-400" />
                  Report History
                </h2>
                <button
                  onClick={() => setView('main')}
                  className="text-sm text-slate-400 hover:text-white cursor-pointer"
                >
                  Back
                </button>
              </div>

              <div className="space-y-3">
                {sessions.map((session, index) => (
                  <motion.div
                    key={session.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.03 }}
                    className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-xl p-5"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-xl">{getReasonIcon(session.reason)}</span>
                          <span className="font-semibold text-white">Session #{session.id}</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(session.status)}`}>
                            {session.status.toUpperCase()}
                          </span>
                        </div>
                        
                        <div className="flex flex-wrap gap-2 mb-3">
                          {(Array.isArray(session.targets) ? session.targets.slice(0, 5) : []).map((target, i) => (
                            <span
                              key={i}
                              className="px-2 py-1 bg-white/5 rounded text-xs text-slate-400"
                            >
                              {target}
                            </span>
                          ))}
                          {Array.isArray(session.targets) && session.targets.length > 5 && (
                            <span className="px-2 py-1 bg-white/5 rounded text-xs text-slate-500">
                              +{session.targets.length - 5} more
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="flex items-center gap-3 mb-1">
                          <span className="flex items-center gap-1 text-emerald-400 text-sm">
                            <CheckCircle2 size={14} />
                            {session.successful_reports}
                          </span>
                          <span className="flex items-center gap-1 text-red-400 text-sm">
                            <XCircle size={14} />
                            {session.failed_reports}
                          </span>
                          {(session.skipped_reports || 0) > 0 && (
                            <span className="flex items-center gap-1 text-slate-400 text-sm">
                              <SkipForward size={14} />
                              {session.skipped_reports}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500">
                          {new Date(session.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
