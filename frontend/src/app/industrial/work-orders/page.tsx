'use client';
import { useEffect, useState, useCallback } from 'react';
import { industrialApi, systemApi } from '@/lib/api';
import { ClipboardList, Loader2, ChevronDown, Download } from 'lucide-react';

interface WO {
  wo_id: string; title: string; description: string; type: string; status: string;
  equipment_tag: string | null; incident_id: string | null; created_at: string | null;
}

const STATUSES = ['open', 'planned', 'in_progress', 'completed', 'cancelled'];
const STATUS_COLOR: Record<string, string> = {
  open: '#3b82f6', planned: '#a855f7', in_progress: '#f59e0b', completed: '#22c55e', cancelled: '#64748b',
};

export default function WorkOrdersPage() {
  const [wos, setWos] = useState<WO[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    industrialApi.getWorkOrders().then(d => { setWos(d.work_orders); setLoading(false); }).catch(() => setLoading(false));
  }, []);
  useEffect(() => { load(); }, [load]);

  const changeStatus = async (wo_id: string, status: string) => {
    setWos(ws => ws.map(w => w.wo_id === wo_id ? { ...w, status } : w)); // optimistic
    try { await industrialApi.updateWorkOrderStatus(wo_id, status); } catch { load(); }
  };

  const counts = STATUSES.reduce((acc, s) => ({ ...acc, [s]: wos.filter(w => w.status === s).length }), {} as Record<string, number>);

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8 flex items-start justify-between animate-fade-in-up">
        <div>
          <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
            <ClipboardList size={28} className="inline mr-2" style={{ color: '#f59e0b' }} />
            Work<span className="gradient-text"> Orders</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Track maintenance actions from creation to completion — the loop that closes an AI recommendation.</p>
        </div>
        <button onClick={() => systemApi.exportCsv('work-orders')} className="btn-ghost" style={{ padding: '9px 14px' }}>
          <Download size={15} /> Export CSV
        </button>
      </div>

      {/* Status summary */}
      <div className="flex flex-wrap gap-3 mb-6">
        {STATUSES.map(s => (
          <div key={s} className="industrial-card px-4 py-2 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ background: STATUS_COLOR[s] }} />
            <span className="text-sm capitalize" style={{ color: 'var(--text-secondary)' }}>{s.replace('_', ' ')}</span>
            <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{counts[s] || 0}</span>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)' }}><Loader2 size={16} className="animate-spin" /> Loading work orders…</div>
      ) : wos.length === 0 ? (
        <div className="text-center py-16" style={{ color: 'var(--text-muted)' }}>
          <ClipboardList size={44} className="mx-auto mb-3 opacity-30" />
          <p className="text-lg">No work orders yet.</p>
          <p className="text-sm mt-1">Run a Maintenance analysis and create a work order from a recommendation.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {wos.map(w => (
            <div key={w.wo_id} className="industrial-card p-5 flex items-start gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="text-xs font-mono px-2 py-0.5 rounded" style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--text-secondary)' }}>{w.wo_id}</span>
                  {w.equipment_tag && <span className="text-[11px] font-mono" style={{ color: '#60a5fa' }}>{w.equipment_tag}</span>}
                  <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{w.type}</span>
                  {w.incident_id && <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>· resolves {w.incident_id}</span>}
                </div>
                <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{w.title}</div>
                {w.description && <div className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{w.description}</div>}
              </div>
              <div className="relative flex-shrink-0">
                <select
                  value={w.status}
                  onChange={e => changeStatus(w.wo_id, e.target.value)}
                  className="pl-3 pr-8 py-2 rounded-lg text-xs font-semibold outline-none appearance-none cursor-pointer capitalize"
                  style={{ background: `${STATUS_COLOR[w.status] || '#3b82f6'}1f`, color: STATUS_COLOR[w.status] || '#3b82f6', border: `1px solid ${STATUS_COLOR[w.status] || '#3b82f6'}44` }}
                >
                  {STATUSES.map(s => <option key={s} value={s} style={{ background: '#111827', color: '#fff' }}>{s.replace('_', ' ')}</option>)}
                </select>
                <ChevronDown size={13} className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: STATUS_COLOR[w.status] || '#3b82f6' }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
