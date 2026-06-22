import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,
  ArrowLeft,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Clock,
  Zap,
  CheckCircle2,
  Lightbulb,
  Target,
  Users,
  Calendar,
  Award,
  Coffee,
  Activity,
} from 'lucide-react';

interface AnalyticsDashboardProps {
  onBack: () => void;
}

interface Insight {
  insights: string[];
  recommendations: string[];
  success_rate: number;
  total_reports: number;
}

interface HourData {
  hour: number;
  hour_formatted: string;
  success_rate: number;
  total_reports: number;
}

interface AccountRanking {
  account_id: string;
  phone: string;
  total_reports: number;
  successful: number;
  success_rate: number;
  health_score: number;
  flood_waits: number;
}

interface DailyTrend {
  date: string;
  reports: number;
}

interface ReasonEffectiveness {
  reason: string;
  total: number;
  successful: number;
  success_rate: number;
}

export default function AnalyticsDashboard({ onBack }: AnalyticsDashboardProps) {
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState<Insight | null>(null);
  const [bestHours, setBestHours] = useState<HourData[]>([]);
  const [worstHours, setWorstHours] = useState<HourData[]>([]);
  const [accountRankings, setAccountRankings] = useState<AccountRanking[]>([]);
  const [accountsNeedingRest, setAccountsNeedingRest] = useState<string[]>([]);
  const [dailyTrend, setDailyTrend] = useState<DailyTrend[]>([]);
  const [reasonEffectiveness, setReasonEffectiveness] = useState<ReasonEffectiveness[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch analytics dashboard
      const response = await fetch('http://localhost:8000/api/analytics/dashboard');
      const data = await response.json();
      
      if (data.success) {
        setInsights(data.insights);
        setBestHours(data.best_hours || []);
        setWorstHours(data.worst_hours || []);
        setAccountRankings(data.account_rankings || []);
        setAccountsNeedingRest(data.accounts_needing_rest || []);
        setDailyTrend(data.daily_trend || []);
        setReasonEffectiveness(data.reason_effectiveness || []);
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400';
    if (score >= 60) return 'text-amber-400';
    return 'text-red-400';
  };

  const getHealthBg = (score: number) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 60) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const maxTrendValue = Math.max(...dailyTrend.map(d => d.reports), 1);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <RefreshCw size={32} className="text-sky-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
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
                <BarChart3 className="text-blue-400" />
                Analytics Dashboard
              </h1>
              <p className="text-sm text-slate-400">
                Insights and performance metrics
              </p>
            </div>
          </div>

          <button
            onClick={fetchData}
            className="p-2.5 bg-white/5 border border-white/10 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-all cursor-pointer"
          >
            <RefreshCw size={16} />
          </button>
        </motion.div>

        {/* Overview Stats */}
        {insights && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
          >
            <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-2">
                <Activity size={20} className="text-blue-400" />
                <span className={`text-sm ${insights.success_rate >= 70 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {insights.success_rate >= 70 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                </span>
              </div>
              <p className="text-3xl font-bold text-white">{insights.success_rate}%</p>
              <p className="text-xs text-slate-500">Success Rate</p>
            </div>

            <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-2">
                <Target size={20} className="text-purple-400" />
              </div>
              <p className="text-3xl font-bold text-white">{insights.total_reports.toLocaleString()}</p>
              <p className="text-xs text-slate-500">Total Reports</p>
            </div>

            <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-2">
                <Users size={20} className="text-emerald-400" />
              </div>
              <p className="text-3xl font-bold text-white">{accountRankings.length}</p>
              <p className="text-xs text-slate-500">Active Accounts</p>
            </div>

            <div className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-5">
              <div className="flex items-center justify-between mb-2">
                <Coffee size={20} className="text-amber-400" />
              </div>
              <p className="text-3xl font-bold text-white">{accountsNeedingRest.length}</p>
              <p className="text-xs text-slate-500">Accounts Need Rest</p>
            </div>
          </motion.div>
        )}

        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* AI Insights */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2 bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6"
          >
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Lightbulb className="text-amber-400" />
              AI Insights
            </h2>
            
            {insights && (
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Observations</p>
                  <div className="space-y-2">
                    {insights.insights.map((insight, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-slate-300">
                        <CheckCircle2 size={14} className="text-emerald-400 mt-1 flex-shrink-0" />
                        <span>{insight}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                {insights.recommendations.length > 0 && (
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wide mb-2">Recommendations</p>
                    <div className="space-y-2">
                      {insights.recommendations.map((rec, i) => (
                        <div key={i} className="flex items-start gap-2 text-sm text-slate-300">
                          <Zap size={14} className="text-amber-400 mt-1 flex-shrink-0" />
                          <span>{rec}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.div>

          {/* Best/Worst Hours */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6"
          >
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Clock className="text-blue-400" />
              Timing Insights
            </h2>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs text-emerald-400 uppercase tracking-wide mb-2">✓ Best Hours</p>
                <div className="space-y-2">
                  {bestHours.slice(0, 3).map((hour, i) => (
                    <div key={i} className="flex items-center justify-between p-2 bg-emerald-500/10 rounded-lg">
                      <span className="text-sm text-white">{hour.hour_formatted}</span>
                      <span className="text-sm text-emerald-400">{hour.success_rate}%</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <p className="text-xs text-red-400 uppercase tracking-wide mb-2">✗ Avoid</p>
                <div className="space-y-2">
                  {worstHours.slice(0, 2).map((hour, i) => (
                    <div key={i} className="flex items-center justify-between p-2 bg-red-500/10 rounded-lg">
                      <span className="text-sm text-white">{hour.hour_formatted}</span>
                      <span className="text-sm text-red-400">{hour.success_rate}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Daily Trend Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6 mb-8"
        >
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Calendar className="text-purple-400" />
            Daily Report Volume
          </h2>
          
          <div className="flex items-end gap-2 h-32">
            {dailyTrend.map((day, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div className="w-full bg-white/5 rounded-t relative" style={{ height: '100px' }}>
                  <div
                    className="absolute bottom-0 w-full bg-gradient-to-t from-blue-600 to-blue-400 rounded-t transition-all duration-500"
                    style={{ height: `${(day.reports / maxTrendValue) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-slate-500">{day.date.slice(5)}</span>
                <span className="text-xs text-white font-medium">{day.reports}</span>
              </div>
            ))}
          </div>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Account Rankings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6"
          >
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Award className="text-amber-400" />
              Account Performance
            </h2>
            
            <div className="space-y-3">
              {accountRankings.slice(0, 6).map((account, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-white/5 rounded-xl">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    i === 0 ? 'bg-amber-500/20 text-amber-400' :
                    i === 1 ? 'bg-slate-400/20 text-slate-300' :
                    i === 2 ? 'bg-orange-600/20 text-orange-400' :
                    'bg-white/10 text-slate-400'
                  }`}>
                    {i + 1}
                  </div>
                  
                  <div className="flex-1">
                    <p className="text-sm text-white">{account.phone}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-slate-500">{account.total_reports} reports</span>
                      <span className="text-xs text-emerald-400">{account.success_rate}%</span>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <p className={`text-lg font-bold ${getHealthColor(account.health_score)}`}>
                      {Math.round(account.health_score)}
                    </p>
                    <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${getHealthBg(account.health_score)} transition-all`}
                        style={{ width: `${account.health_score}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
              
              {accountRankings.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-8">
                  No account data yet
                </p>
              )}
            </div>
          </motion.div>

          {/* Reason Effectiveness */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6"
          >
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="text-red-400" />
              Reason Effectiveness
            </h2>
            
            <div className="space-y-3">
              {reasonEffectiveness.map((reason, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white capitalize">{reason.reason.replace('_', ' ')}</span>
                    <span className={`text-sm font-medium ${
                      reason.success_rate >= 70 ? 'text-emerald-400' :
                      reason.success_rate >= 50 ? 'text-amber-400' :
                      'text-red-400'
                    }`}>
                      {reason.success_rate}%
                    </span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        reason.success_rate >= 70 ? 'bg-emerald-500' :
                        reason.success_rate >= 50 ? 'bg-amber-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${reason.success_rate}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-500">
                    {reason.successful} / {reason.total} successful
                  </p>
                </div>
              ))}
              
              {reasonEffectiveness.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-8">
                  No reason data yet
                </p>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
