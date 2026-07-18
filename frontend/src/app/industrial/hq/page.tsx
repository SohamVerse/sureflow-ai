'use client';
import { useEffect, useState } from 'react';
import { hqApi } from '@/lib/api';
import { useAuth } from '@/lib/AuthContext';
import {
  Globe, Cpu, AlertTriangle, Wrench, ClipboardCheck, FileText, Lightbulb,
  Building2, ShieldAlert, Loader2, Trophy, MessageSquare, Send,
} from 'lucide-react';

interface PlantMetric {
  plant_id: string;
  name: string;
  location: string;
  status: string;
  stats: Record<string, number>;
  critical_incidents: number;
  high_incidents: number;
  lessons_count: number;
  risk_index: number;
}
interface Overview {
  total_plants: number;
  totals: Record<string, number>;
  plants: PlantMetric[];
  highest_risk_plant: string | null;
}

const TOTAL_TILES: Array<{ key: string; label: string; icon: typeof Cpu; color: string }> = [
  { key: 'equipment', label: 'Total Equipment', icon: Cpu, color: '#a855f7' },
  { key: 'incidents', label: 'Open Incidents', icon: AlertTriangle, color: '#ef4444' },
  { key: 'work_orders', label: 'Work Orders', icon: Wrench, color: '#f59e0b' },
  { key: 'inspections', label: 'Inspections', icon: ClipboardCheck, color: '#22c55e' },
  { key: 'documents', label: 'Documents', icon: FileText, color: '#a855f7' },
  { key: 'lessons', label: 'Lessons Learned', icon: Lightbulb, color: '#eab308' },
];

function riskColor(r: number) {
  return r >= 2 ? '#ef4444' : r >= 0.5 ? '#f59e0b' : '#22c55e';
}

export default function HQOverviewPage() {
  const { user } = useAuth();
  const [data, setData] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);
  const [ranking, setRanking] = useState<any[]>([]);

  // HQ Copilot (global — asks across all plants)
  const [q, setQ] = useState('');
  const [answer, setAnswer] = useState('');
  const [asking, setAsking] = useState(false);

  useEffect(() => {
    hqApi.overview().then(d => { setData(d as Overview); setLoading(false); }).catch(() => setLoading(false));
    hqApi.benchmark().then(d => setRanking(d.ranking)).catch(() => {});
  }, []);

  const askHQ = async () => {
    if (!q.trim()) return;
    setAsking(true); setAnswer('');
    try {
      const res = await hqApi.copilot(q.trim());
      setAnswer(res.answer || res.summary || 'No answer.');
    } catch {
      setAnswer('⚠️ Copilot error — check the backend and LLM quota.');
    }
    setAsking(false);
  };

  if (user && user.role !== 'cto') {
    return (
      <div className="p-8 min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-primary)' }}>
        <div className="text-center">
          <ShieldAlert size={40} className="mx-auto mb-3 opacity-40" style={{ color: 'var(--text-muted)' }} />
          <p style={{ color: 'var(--text-secondary)' }}>HQ view is available to global (CTO) accounts only.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <Globe size={28} className="inline mr-2" style={{ color: '#a855f7' }} />
          Headquarters<span className="gradient-text"> Overview</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Enterprise roll-up across all plants — {data?.total_plants ?? '…'} location{data?.total_plants === 1 ? '' : 's'}.
        </p>
      </div>

      {loading ? (
        <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)' }}>
          <Loader2 size={16} className="animate-spin" /> Loading enterprise metrics…
        </div>
      ) : !data ? (
        <p style={{ color: 'var(--text-muted)' }}>Could not load HQ data.</p>
      ) : (
        <>
          {/* Aggregate tiles */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            {TOTAL_TILES.map((t, i) => (
              <div key={t.key} className="industrial-card p-5 animate-fade-in-up" style={{ animationDelay: `${i * 0.04}s` }}>
                <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-3" style={{ background: `${t.color}1f` }}>
                  <t.icon size={16} style={{ color: t.color }} />
                </div>
                <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{data.totals[t.key] ?? 0}</div>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{t.label}</div>
              </div>
            ))}
          </div>

          {/* Per-plant cards */}
          <h2 className="font-semibold text-lg mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <Building2 size={18} style={{ color: '#a855f7' }} /> Plants
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {data.plants.map((p, i) => {
              const isRisk = p.plant_id === data.highest_risk_plant && p.risk_index > 0;
              return (
                <div key={p.plant_id} className="industrial-card p-6 animate-fade-in-up" style={{ animationDelay: `${i * 0.05}s`, borderColor: isRisk ? 'rgba(239,68,68,0.3)' : undefined }}>
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="font-semibold" style={{ color: 'var(--text-primary)' }}>{p.name}</div>
                      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{p.location || p.plant_id}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Risk</div>
                      <div className="text-lg font-bold" style={{ color: riskColor(p.risk_index) }}>{p.risk_index}</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    {[
                      { label: 'Equipment', v: p.stats.equipment ?? 0 },
                      { label: 'Incidents', v: p.stats.incidents ?? 0 },
                      { label: 'Critical', v: p.critical_incidents },
                      { label: 'Work Orders', v: p.stats.work_orders ?? 0 },
                      { label: 'Inspections', v: p.stats.inspections ?? 0 },
                      { label: 'Lessons', v: p.lessons_count },
                    ].map(m => (
                      <div key={m.label} className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)' }}>
                        <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{m.v}</div>
                        <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{m.label}</div>
                      </div>
                    ))}
                  </div>
                  {isRisk && (
                    <div className="mt-3 flex items-center gap-2 text-xs" style={{ color: '#ef4444' }}>
                      <ShieldAlert size={13} /> Highest-risk plant
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Benchmark ranking + HQ Copilot */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
            {/* Reliability leaderboard */}
            <div className="industrial-card p-6">
              <h2 className="font-semibold text-lg mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                <Trophy size={18} style={{ color: '#eab308' }} /> Reliability Ranking
              </h2>
              <div className="space-y-2">
                {ranking.map(r => (
                  <div key={r.plant_id} className="flex items-center gap-3 p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)' }}>
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center text-sm font-bold" style={{
                      background: r.rank === 1 ? 'rgba(234,179,8,0.15)' : 'rgba(255,255,255,0.04)',
                      color: r.rank === 1 ? '#eab308' : 'var(--text-secondary)',
                    }}>{r.rank}</div>
                    <div className="flex-1">
                      <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{r.name}</div>
                      <div className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{r.stats.equipment} equipment · {r.critical_incidents} critical</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold" style={{ color: r.reliability_score >= 80 ? '#22c55e' : r.reliability_score >= 50 ? '#f59e0b' : '#ef4444' }}>{r.reliability_score}</div>
                      <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>score</div>
                    </div>
                  </div>
                ))}
                {ranking.length === 0 && <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No ranking data.</p>}
              </div>
            </div>

            {/* HQ Copilot — ask across all plants */}
            <div className="industrial-card p-6 flex flex-col">
              <h2 className="font-semibold text-lg mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                <MessageSquare size={18} style={{ color: '#14b8a6' }} /> HQ Copilot
                <span className="text-[10px] font-normal px-2 py-0.5 rounded-full" style={{ background: 'rgba(20,184,166,0.12)', color: '#2dd4bf' }}>all plants</span>
              </h2>
              <div className="flex gap-2 mb-3">
                <input
                  value={q}
                  onChange={e => setQ(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && askHQ()}
                  placeholder="e.g. Which plant has the worst compliance posture?"
                  className="flex-1 px-3 py-2.5 rounded-lg text-sm outline-none"
                  style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
                />
                <button onClick={askHQ} disabled={asking} className="btn-primary" style={{ padding: '0 14px' }}>
                  {asking ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                </button>
              </div>
              <div className="flex-1 p-4 rounded-lg overflow-y-auto text-sm copilot-markdown" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)', color: 'var(--text-secondary)', minHeight: '140px', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                {asking ? 'Thinking across all plants…' : (answer || 'Ask a question spanning every plant — the Copilot reasons over the whole enterprise.')}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
