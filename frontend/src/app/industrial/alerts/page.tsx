'use client';
import { useEffect, useState, useCallback } from 'react';
import { alertsApi } from '@/lib/api';
import {
  Bell, AlertTriangle, ClipboardCheck, ShieldAlert, Wrench, RefreshCw,
  Check, CheckCheck, Loader2, Sunrise,
} from 'lucide-react';

interface Alert {
  id: string; plant_id: string | null; severity: string; category: string;
  title: string; message: string; equipment_tag: string | null; status: string; created_at: string | null;
}

const SEV_COLOR: Record<string, string> = { critical: '#ef4444', high: '#f59e0b', medium: '#3b82f6', low: '#22c55e' };
const CAT_ICON: Record<string, typeof AlertTriangle> = { incident: AlertTriangle, inspection: ClipboardCheck, compliance: ShieldAlert, maintenance: Wrench };

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [filter, setFilter] = useState<string>('open'); // open | all | resolved
  const [digest, setDigest] = useState<any>(null);

  const load = useCallback(() => {
    setLoading(true);
    const statusParam = filter === 'all' ? undefined : filter === 'resolved' ? 'resolved' : undefined;
    alertsApi.list(statusParam).then(d => {
      let a = d.alerts as Alert[];
      if (filter === 'open') a = a.filter(x => x.status !== 'resolved');
      setAlerts(a); setLoading(false);
    }).catch(() => setLoading(false));
  }, [filter]);

  useEffect(() => { load(); }, [load]);
  // Proactive briefing (also refreshes alerts server-side via generate).
  useEffect(() => { alertsApi.digest().then(setDigest).catch(() => {}); }, []);

  const rescan = async () => {
    setScanning(true);
    try { await alertsApi.generate(); load(); } catch { /* ignore */ }
    setScanning(false);
  };

  const act = async (id: string, kind: 'ack' | 'resolve') => {
    try { kind === 'ack' ? await alertsApi.ack(id) : await alertsApi.resolve(id); load(); } catch { /* ignore */ }
  };

  const openCount = alerts.filter(a => a.status === 'new').length;

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8 flex items-start justify-between animate-fade-in-up">
        <div>
          <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
            <Bell size={28} className="inline mr-2" style={{ color: '#ef4444' }} />
            Proactive<span className="gradient-text"> Alerts</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            {openCount > 0 ? `${openCount} open alert${openCount > 1 ? 's' : ''} need attention.` : 'No open alerts — all clear.'}
          </p>
        </div>
        <button onClick={rescan} disabled={scanning} className="btn-primary" style={{ padding: '10px 16px' }}>
          {scanning ? <><Loader2 size={16} className="animate-spin" /> Scanning…</> : <><RefreshCw size={16} /> Re-scan</>}
        </button>
      </div>

      {/* Proactive briefing (daily risk digest) */}
      {digest && (
        <div className="industrial-card p-5 mb-6 animate-fade-in-up" style={{ borderColor: 'rgba(99,102,241,0.25)' }}>
          <div className="flex items-center gap-2 mb-3">
            <Sunrise size={18} style={{ color: '#818cf8' }} />
            <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>Today&apos;s Risk Briefing</span>
            <span className="text-[10px] font-normal px-2 py-0.5 rounded-full" style={{ background: 'rgba(99,102,241,0.12)', color: '#818cf8' }}>proactive</span>
          </div>
          <p className="text-sm mb-3" style={{ color: 'var(--text-secondary)' }}>{digest.headline}</p>
          {digest.priorities?.length > 0 && (
            <ol className="space-y-1.5">
              {digest.priorities.slice(0, 5).map((p: any) => (
                <li key={p.rank} className="flex items-start gap-2 text-xs">
                  <span className="font-bold" style={{ color: p.severity === 'critical' ? '#ef4444' : p.severity === 'high' ? '#f59e0b' : '#3b82f6' }}>{p.rank}.</span>
                  <span style={{ color: 'var(--text-primary)' }}>{p.title}</span>
                  <span style={{ color: 'var(--text-muted)' }}>— {p.recommended_action}</span>
                </li>
              ))}
            </ol>
          )}
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6">
        {(['open', 'all', 'resolved'] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)} className="px-4 py-2 rounded-xl text-sm font-medium capitalize transition-all"
            style={{
              background: filter === f ? 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(6,182,212,0.12))' : 'rgba(255,255,255,0.03)',
              border: `1px solid ${filter === f ? 'var(--border-active)' : 'var(--border)'}`,
              color: filter === f ? 'var(--text-primary)' : 'var(--text-secondary)',
            }}>{f}</button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)' }}><Loader2 size={16} className="animate-spin" /> Loading alerts…</div>
      ) : alerts.length === 0 ? (
        <div className="text-center py-16" style={{ color: 'var(--text-muted)' }}>
          <CheckCheck size={44} className="mx-auto mb-3 opacity-30" />
          <p className="text-lg">No alerts here.</p>
          <p className="text-sm mt-1">Hit “Re-scan” to check the knowledge graph for new signals.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map(a => {
            const Icon = CAT_ICON[a.category] || AlertTriangle;
            const color = SEV_COLOR[a.severity] || '#3b82f6';
            const resolved = a.status === 'resolved';
            return (
              <div key={a.id} className="industrial-card p-5 flex items-start gap-4" style={{ opacity: resolved ? 0.55 : 1, borderColor: `${color}33` }}>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: `${color}1f` }}>
                  <Icon size={18} style={{ color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="badge" style={{ background: `${color}1f`, color, border: `1px solid ${color}44` }}>{a.severity}</span>
                    <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{a.category}</span>
                    {a.equipment_tag && <span className="text-[10px] font-mono px-2 py-0.5 rounded" style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--text-secondary)' }}>{a.equipment_tag}</span>}
                    {a.plant_id && <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>· {a.plant_id}</span>}
                    {a.status !== 'new' && <span className="text-[10px] font-semibold" style={{ color: a.status === 'resolved' ? '#22c55e' : '#f59e0b' }}>· {a.status}</span>}
                  </div>
                  <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{a.title}</div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{a.message}</div>
                </div>
                {!resolved && (
                  <div className="flex gap-2 flex-shrink-0">
                    {a.status === 'new' && (
                      <button onClick={() => act(a.id, 'ack')} title="Acknowledge" className="p-2 rounded-lg" style={{ background: 'rgba(245,158,11,0.12)', color: '#f59e0b' }}><Check size={15} /></button>
                    )}
                    <button onClick={() => act(a.id, 'resolve')} title="Resolve" className="p-2 rounded-lg" style={{ background: 'rgba(34,197,94,0.12)', color: '#22c55e' }}><CheckCheck size={15} /></button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
