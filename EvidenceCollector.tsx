import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Camera,
  ArrowLeft,
  RefreshCw,
  Plus,
  Download,
  Trash2,
  MessageSquare,
  Image,
  User,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Package,
  Eye,
  Search,
} from 'lucide-react';
import { api } from '../api';
import GlowButton from './GlowButton';

interface EvidenceCollectorProps {
  onBack: () => void;
}

interface EvidencePackage {
  id: string;
  target: string;
  target_name: string | null;
  target_type: string | null;
  target_id: number | null;
  bio: string | null;
  message_count: number;
  photo_count: number;
  media_count: number;
  member_count: number | null;
  collected_at: string;
  duration_seconds: number;
  evidence_count: number;
  status: string;
  error: string | null;
  has_profile: boolean;
  has_messages: boolean;
  has_photos: boolean;
  export_path: string | null;
  profile_info?: Record<string, unknown>;
  messages_preview?: Array<{ text: string; date: string }>;
}

interface Account {
  id: string;
  phone: string;
  firstName: string;
}

interface EvidenceStats {
  total_packages: number;
  completed: number;
  failed: number;
  total_messages: number;
  total_photos: number;
  exported: number;
}

export default function EvidenceCollector({ onBack }: EvidenceCollectorProps) {
  const [view, setView] = useState<'list' | 'new' | 'detail'>('list');
  const [loading, setLoading] = useState(true);
  const [packages, setPackages] = useState<EvidencePackage[]>([]);
  const [stats, setStats] = useState<EvidenceStats | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedPkg, setSelectedPkg] = useState<EvidencePackage | null>(null);
  
  // Collection form
  const [target, setTarget] = useState('');
  const [selectedAccount, setSelectedAccount] = useState('');
  const [collectMessages, setCollectMessages] = useState(true);
  const [collectPhotos, setCollectPhotos] = useState(true);
  const [maxMessages, setMaxMessages] = useState(50);
  const [collecting, setCollecting] = useState(false);
  const [collectResult, setCollectResult] = useState<{ success: boolean; message: string } | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [evidenceRes, accountsRes] = await Promise.all([
        fetch('http://localhost:8000/api/evidence'),
        api.getAccounts(),
      ]);
      const evidenceData = await evidenceRes.json();
      if (evidenceData.success) {
        setPackages(evidenceData.packages || []);
        setStats(evidenceData.stats);
      }
      if (accountsRes.success) {
        setAccounts(accountsRes.accounts.map(a => ({ id: a.id, phone: a.phone, firstName: a.firstName })));
        if (accountsRes.accounts.length > 0 && !selectedAccount) {
          setSelectedAccount(accountsRes.accounts[0].id);
        }
      }
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  }, [selectedAccount]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCollect = async () => {
    if (!target.trim() || !selectedAccount) return;
    setCollecting(true);
    setCollectResult(null);
    try {
      const res = await fetch('http://localhost:8000/api/evidence/collect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target: target.trim(),
          account_id: selectedAccount,
          collect_messages: collectMessages,
          collect_photos: collectPhotos,
          max_messages: maxMessages,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setCollectResult({ success: true, message: `Evidence collected! ${data.package.evidence_count} items` });
        setTarget('');
        setTimeout(() => { setView('list'); fetchData(); }, 1500);
      } else {
        setCollectResult({ success: false, message: data.error || 'Collection failed' });
      }
    } catch {
      setCollectResult({ success: false, message: 'Network error' });
    }
    setCollecting(false);
  };

  const handleExport = async (pkgId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/evidence/${pkgId}/export`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        // Download the file
        window.open(`http://localhost:8000/api/evidence/${pkgId}/download`, '_blank');
      }
    } catch (error) {
      console.error('Export error:', error);
    }
  };

  const handleDelete = async (pkgId: string) => {
    if (!confirm('Delete this evidence package?')) return;
    await fetch(`http://localhost:8000/api/evidence/${pkgId}`, { method: 'DELETE' });
    await fetchData();
    if (selectedPkg?.id === pkgId) { setSelectedPkg(null); setView('list'); }
  };

  const handleViewDetail = async (pkgId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/evidence/${pkgId}`);
      const data = await res.json();
      if (data.success) {
        setSelectedPkg(data.package);
        setView('detail');
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': case 'exported': return 'text-emerald-400 bg-emerald-500/10';
      case 'collecting': return 'text-amber-400 bg-amber-500/10';
      case 'failed': return 'text-red-400 bg-red-500/10';
      default: return 'text-slate-400 bg-slate-500/10';
    }
  };

  if (loading && !stats) {
    return <div className="min-h-screen flex items-center justify-center"><RefreshCw size={32} className="text-amber-400 animate-spin" /></div>;
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-orange-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-6xl mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button onClick={view === 'detail' ? () => setView('list') : onBack} className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all cursor-pointer">
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-3">
                <Camera className="text-amber-400" />
                Evidence Collector
              </h1>
              <p className="text-sm text-slate-400">Collect proof before reporting</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={fetchData} className="p-2.5 bg-white/5 border border-white/10 rounded-xl text-slate-400 hover:text-white transition-all cursor-pointer">
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
            <GlowButton onClick={() => setView('new')}>
              <Plus size={18} /> Collect
            </GlowButton>
          </div>
        </motion.div>

        {/* Stats */}
        {stats && view === 'list' && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-3 md:grid-cols-6 gap-3 mb-8">
            {[
              { label: 'Packages', value: stats.total_packages, icon: Package, color: 'amber' },
              { label: 'Completed', value: stats.completed, icon: CheckCircle2, color: 'emerald' },
              { label: 'Failed', value: stats.failed, icon: XCircle, color: 'red' },
              { label: 'Messages', value: stats.total_messages, icon: MessageSquare, color: 'sky' },
              { label: 'Photos', value: stats.total_photos, icon: Image, color: 'purple' },
              { label: 'Exported', value: stats.exported, icon: Download, color: 'blue' },
            ].map((s) => (
              <div key={s.label} className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-3 text-center">
                <div className={`inline-flex items-center justify-center w-8 h-8 rounded-lg mb-1 ${{
                  amber: 'bg-amber-500/10 text-amber-400', emerald: 'bg-emerald-500/10 text-emerald-400',
                  red: 'bg-red-500/10 text-red-400', sky: 'bg-sky-500/10 text-sky-400',
                  purple: 'bg-purple-500/10 text-purple-400', blue: 'bg-blue-500/10 text-blue-400',
                }[s.color]}`}><s.icon size={16} /></div>
                <p className="text-xl font-bold text-white">{s.value}</p>
                <p className="text-[10px] text-slate-500">{s.label}</p>
              </div>
            ))}
          </motion.div>
        )}

        {/* New Collection Form */}
        <AnimatePresence>
          {view === 'new' && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="max-w-lg mx-auto">
              <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6 space-y-5">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-white flex items-center gap-2"><Search size={18} className="text-amber-400" /> Collect Evidence</h2>
                  <button onClick={() => setView('list')} className="text-sm text-slate-400 hover:text-white cursor-pointer">Cancel</button>
                </div>

                <div>
                  <label className="text-sm text-slate-300 mb-1 block">Target</label>
                  <input type="text" value={target} onChange={(e) => setTarget(e.target.value)} placeholder="@username or t.me/channel"
                    className="w-full px-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white placeholder-slate-600 text-sm focus:outline-none focus:border-amber-500/50" />
                </div>

                <div>
                  <label className="text-sm text-slate-300 mb-1 block">Account to Use</label>
                  <select value={selectedAccount} onChange={(e) => setSelectedAccount(e.target.value)}
                    className="w-full px-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-amber-500/50 cursor-pointer">
                    {accounts.map(a => <option key={a.id} value={a.id}>{a.firstName} ({a.phone})</option>)}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <label className="flex items-center gap-2 p-3 bg-white/5 rounded-xl cursor-pointer">
                    <input type="checkbox" checked={collectMessages} onChange={(e) => setCollectMessages(e.target.checked)} className="w-4 h-4 rounded" />
                    <div><p className="text-sm text-white">Messages</p><p className="text-xs text-slate-500">Up to {maxMessages}</p></div>
                  </label>
                  <label className="flex items-center gap-2 p-3 bg-white/5 rounded-xl cursor-pointer">
                    <input type="checkbox" checked={collectPhotos} onChange={(e) => setCollectPhotos(e.target.checked)} className="w-4 h-4 rounded" />
                    <div><p className="text-sm text-white">Photos</p><p className="text-xs text-slate-500">Profile pics</p></div>
                  </label>
                </div>

                {collectMessages && (
                  <div>
                    <label className="text-sm text-slate-300 mb-1 block">Max Messages: {maxMessages}</label>
                    <input type="range" min={10} max={200} value={maxMessages} onChange={(e) => setMaxMessages(Number(e.target.value))}
                      className="w-full accent-amber-500" />
                  </div>
                )}

                {collectResult && (
                  <div className={`p-3 rounded-xl flex items-center gap-2 ${collectResult.success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                    {collectResult.success ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                    <span className="text-sm">{collectResult.message}</span>
                  </div>
                )}

                <GlowButton onClick={handleCollect} disabled={collecting || !target.trim()} className="w-full">
                  {collecting ? <><Loader2 size={18} className="animate-spin" /> Collecting...</> : <><Camera size={18} /> Collect Evidence</>}
                </GlowButton>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Package List */}
        {view === 'list' && (
          <div className="space-y-3">
            {packages.length === 0 ? (
              <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-3xl p-12 text-center">
                <Camera size={40} className="text-amber-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-white mb-2">No Evidence Collected</h3>
                <p className="text-sm text-slate-400 mb-6">Collect evidence from targets before reporting them</p>
                <GlowButton onClick={() => setView('new')}><Plus size={18} /> Collect Evidence</GlowButton>
              </div>
            ) : (
              packages.map((pkg, i) => (
                <motion.div key={pkg.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}
                  className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-xl p-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-400">
                        {pkg.target_type === 'channel' ? <MessageSquare size={20} /> : pkg.target_type === 'group' ? <User size={20} /> : <User size={20} />}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white">{pkg.target_name || pkg.target}</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(pkg.status)}`}>{pkg.status.toUpperCase()}</span>
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                          <span>@{pkg.target}</span>
                          {pkg.has_messages && <span className="flex items-center gap-1"><MessageSquare size={10} />{pkg.message_count}</span>}
                          {pkg.has_photos && <span className="flex items-center gap-1"><Image size={10} />{pkg.photo_count}</span>}
                          <span className="flex items-center gap-1"><Clock size={10} />{pkg.duration_seconds}s</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button onClick={() => handleViewDetail(pkg.id)} className="p-2 rounded-lg bg-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition-all cursor-pointer" title="View details"><Eye size={14} /></button>
                      <button onClick={() => handleExport(pkg.id)} className="p-2 rounded-lg bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 transition-all cursor-pointer" title="Export ZIP"><Download size={14} /></button>
                      <button onClick={() => handleDelete(pkg.id)} className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-all cursor-pointer" title="Delete"><Trash2 size={14} /></button>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        )}

        {/* Detail View */}
        <AnimatePresence>
          {view === 'detail' && selectedPkg && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <div className="grid md:grid-cols-2 gap-6">
                {/* Profile */}
                <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><User size={18} className="text-amber-400" /> Profile</h3>
                  {selectedPkg.profile_info ? (
                    <div className="space-y-2">
                      {Object.entries(selectedPkg.profile_info).map(([key, value]) => (
                        value !== null && value !== undefined && (
                          <div key={key} className="flex justify-between py-1.5 border-b border-white/5">
                            <span className="text-xs text-slate-500 capitalize">{key.replace(/_/g, ' ')}</span>
                            <span className="text-xs text-white font-mono">{String(value)}</span>
                          </div>
                        )
                      ))}
                    </div>
                  ) : <p className="text-sm text-slate-500">No profile data</p>}
                  
                  {selectedPkg.bio && (
                    <div className="mt-4 p-3 bg-white/5 rounded-xl">
                      <p className="text-xs text-slate-400 mb-1">Bio:</p>
                      <p className="text-sm text-white">{selectedPkg.bio}</p>
                    </div>
                  )}
                </div>

                {/* Messages Preview */}
                <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><MessageSquare size={18} className="text-sky-400" /> Messages ({selectedPkg.message_count})</h3>
                  {selectedPkg.messages_preview && selectedPkg.messages_preview.length > 0 ? (
                    <div className="space-y-3 max-h-80 overflow-y-auto">
                      {selectedPkg.messages_preview.map((msg, i) => (
                        <div key={i} className="p-3 bg-white/5 rounded-xl">
                          <p className="text-xs text-slate-500 mb-1">{msg.date}</p>
                          <p className="text-sm text-white">{msg.text || '[media]'}</p>
                        </div>
                      ))}
                    </div>
                  ) : <p className="text-sm text-slate-500">No messages collected</p>}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 mt-6">
                <GlowButton onClick={() => handleExport(selectedPkg.id)} className="flex-1">
                  <Download size={18} /> Export ZIP Package
                </GlowButton>
                <GlowButton onClick={() => handleDelete(selectedPkg.id)} variant="danger">
                  <Trash2 size={18} /> Delete
                </GlowButton>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
