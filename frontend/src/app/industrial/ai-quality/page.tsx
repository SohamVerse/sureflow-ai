'use client';
import { useEffect, useState } from 'react';
import { systemApi } from '@/lib/api';
import { Gauge, Loader2, Clock, DollarSign, Activity, CheckCircle } from 'lucide-react';

const AGENT_COLOR: Record<string, string> = {
  DOC_INTELLIGENCE: '#a855f7', KG_AGENT: '#a855f7', SEARCH_AGENT: '#14b8a6',
  MAINTENANCE: '#f97316', LESSONS_LEARNED: '#eab308', COMPLIANCE: '#a855f7',
};

export default function AIQualityPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    systemApi.aiQuality().then(d => { setData(d); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const totals = data?.totals || {};

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <Gauge size={28} className="inline mr-2" style={{ color: '#818cf8' }} />
          AI Quality<span className="gradient-text"> &amp; Cost</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Every agent call is scored and costed — here&apos;s the health and spend of the AI layer.</p>
      </div>

      {loading ? (
        <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)' }}><Loader2 size={16} className="animate-spin" /> Loading metrics…</div>
      ) : !data || data.agents.length === 0 ? (
        <p style={{ color: 'var(--text-muted)' }}>No agent runs recorded yet. Run a Copilot query or an analysis first.</p>
      ) : (
        <>
          {/* Totals */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            {[
              { label: 'Total Agent Runs', value: totals.total_runs ?? 0, icon: Activity, color: '#a855f7' },
              { label: 'Total LLM Cost', value: `$${(totals.total_cost ?? 0).toFixed(4)}`, icon: DollarSign, color: '#22c55e' },
              { label: 'Avg Latency', value: `${(totals.avg_latency_ms ?? 0).toLocaleString()} ms`, icon: Clock, color: '#f59e0b' },
            ].map((t, i) => (
              <div key={i} className="industrial-card p-6 animate-fade-in-up" style={{ animationDelay: `${i * 0.05}s` }}>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-3" style={{ background: `${t.color}1f` }}>
                  <t.icon size={18} style={{ color: t.color }} />
                </div>
                <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{t.value}</div>
                <div className="text-sm" style={{ color: 'var(--text-muted)' }}>{t.label}</div>
              </div>
            ))}
          </div>

          {/* Per-agent */}
          <h2 className="font-semibold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>Per-Agent Quality</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-8">
            {data.agents.map((a: any) => {
              const color = AGENT_COLOR[a.agent_id] || '#a855f7';
              return (
                <div key={a.agent_id} className="industrial-card p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
                    <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{a.agent_id}</span>
                    <span className="text-[10px] font-mono ml-auto" style={{ color: 'var(--text-muted)' }}>{a.model}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <Metric label="Runs" value={a.runs} />
                    <Metric label="Avg Confidence" value={`${a.avg_confidence}%`} />
                    <Metric label="Avg Latency" value={`${a.avg_latency_ms.toLocaleString()} ms`} />
                    <Metric label="Cost" value={`$${a.total_cost.toFixed(4)}`} />
                    <Metric label="Schema Valid" value={`${a.schema_valid_rate}%`} />
                    <Metric label="Needs Approval" value={a.human_approvals} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Recent runs */}
          <h2 className="font-semibold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>Recent Runs</h2>
          <div className="industrial-card p-0 overflow-x-auto">
            <table className="w-full text-sm" style={{ borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Agent', 'Confidence', 'Latency', 'Cost', 'Valid'].map(h => (
                    <th key={h} className="text-left p-3 text-xs uppercase tracking-wider" style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.recent.map((r: any, i: number) => (
                  <tr key={i}>
                    <td className="p-3" style={{ color: 'var(--text-primary)', borderBottom: '1px solid var(--border)' }}>{r.agent_id}</td>
                    <td className="p-3" style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)' }}>{r.confidence != null ? `${Math.round(r.confidence)}%` : '—'}</td>
                    <td className="p-3" style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)' }}>{r.latency_ms != null ? `${r.latency_ms.toLocaleString()} ms` : '—'}</td>
                    <td className="p-3" style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)' }}>${(r.cost ?? 0).toFixed(5)}</td>
                    <td className="p-3" style={{ borderBottom: '1px solid var(--border)' }}>
                      {r.schema_valid ? <CheckCircle size={14} style={{ color: '#22c55e' }} /> : <span style={{ color: '#ef4444' }}>✗</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)' }}>
      <div className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{value}</div>
      <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{label}</div>
    </div>
  );
}
