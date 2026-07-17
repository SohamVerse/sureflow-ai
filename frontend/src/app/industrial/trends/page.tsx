'use client';
import { useEffect, useState } from 'react';
import { systemApi } from '@/lib/api';
import { TrendChart } from '@/components/industrial/TrendChart';
import { TrendingUp, Loader2 } from 'lucide-react';

export default function TrendsPage() {
  const [snapshots, setSnapshots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    systemApi.trends(180).then(d => { setSnapshots(d.snapshots); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const labels = snapshots.map(s => s.date);
  const series = (key: string) => snapshots.map(s => s[key] ?? 0);

  const CHARTS: Array<{ title: string; key: string; color: string; good: 'up' | 'down' }> = [
    { title: 'Open Incidents', key: 'incidents', color: '#ef4444', good: 'down' },
    { title: 'Open Alerts', key: 'open_alerts', color: '#f59e0b', good: 'down' },
    { title: 'Equipment Tracked', key: 'equipment', color: '#3b82f6', good: 'up' },
    { title: 'Work Orders', key: 'work_orders', color: '#22c55e', good: 'up' },
    { title: 'Inspections', key: 'inspections', color: '#06b6d4', good: 'up' },
    { title: 'Lessons Captured', key: 'lessons', color: '#eab308', good: 'up' },
  ];

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <TrendingUp size={28} className="inline mr-2" style={{ color: '#22c55e' }} />
          KPI<span className="gradient-text"> Trends</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>How the plant is trending over time — not just today&apos;s snapshot. Green delta = improving.</p>
      </div>

      {loading ? (
        <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)' }}><Loader2 size={16} className="animate-spin" /> Loading history…</div>
      ) : snapshots.length === 0 ? (
        <div className="text-center py-16" style={{ color: 'var(--text-muted)' }}>
          <TrendingUp size={44} className="mx-auto mb-3 opacity-30" />
          <p className="text-lg">No history yet.</p>
          <p className="text-sm mt-1">KPI snapshots are captured on a schedule; seed some history to see trends.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {CHARTS.map(c => (
            <TrendChart key={c.key} title={c.title} data={series(c.key)} labels={labels} color={c.color} goodDirection={c.good} />
          ))}
        </div>
      )}
    </div>
  );
}
