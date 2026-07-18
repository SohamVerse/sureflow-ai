'use client';
import { useEffect, useState } from 'react';
import { hqApi, authApi } from '@/lib/api';
import { useAuth } from '@/lib/AuthContext';
import { BarChart3, ShieldAlert, Loader2 } from 'lucide-react';

interface PlantMetric {
  plant_id: string;
  name: string;
  stats: Record<string, number>;
  critical_incidents: number;
  high_incidents: number;
  lessons_count: number;
  risk_index: number;
}

// Rows of the comparison table: label + how to pull the value from a plant metric.
const ROWS: Array<{ label: string; get: (m: PlantMetric) => number; highlight?: 'low' | 'high' }> = [
  { label: 'Equipment', get: m => m.stats.equipment ?? 0 },
  { label: 'Areas', get: m => m.stats.areas ?? 0 },
  { label: 'Open Incidents', get: m => m.stats.incidents ?? 0, highlight: 'low' },
  { label: 'Critical Incidents', get: m => m.critical_incidents, highlight: 'low' },
  { label: 'Work Orders', get: m => m.stats.work_orders ?? 0 },
  { label: 'Inspections', get: m => m.stats.inspections ?? 0, highlight: 'high' },
  { label: 'Documents', get: m => m.stats.documents ?? 0 },
  { label: 'Lessons Learned', get: m => m.lessons_count },
  { label: 'Risk Index', get: m => m.risk_index, highlight: 'low' },
];

export default function ComparePlantsPage() {
  const { user } = useAuth();
  const [plants, setPlants] = useState<Array<{ plant_id: string; name: string }>>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [rows, setRows] = useState<PlantMetric[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    authApi.me().then(d => {
      setPlants(d.plants);
      setSelected(d.plants.slice(0, 2).map(p => p.plant_id)); // default: first two
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (selected.length === 0) { setRows([]); return; }
    setLoading(true);
    hqApi.compare(selected).then(d => { setRows(d.comparison as PlantMetric[]); setLoading(false); }).catch(() => setLoading(false));
  }, [selected]);

  const toggle = (id: string) =>
    setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

  // For each row, find the "best" value to highlight (min for 'low', max for 'high').
  const bestFor = (r: typeof ROWS[number]): number | null => {
    if (!r.highlight || rows.length < 2) return null;
    const vals = rows.map(r.get);
    return r.highlight === 'low' ? Math.min(...vals) : Math.max(...vals);
  };

  if (user && user.role !== 'cto') {
    return (
      <div className="p-8 min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-primary)' }}>
        <div className="text-center">
          <ShieldAlert size={40} className="mx-auto mb-3 opacity-40" style={{ color: 'var(--text-muted)' }} />
          <p style={{ color: 'var(--text-secondary)' }}>Plant comparison is available to global (CTO) accounts only.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <BarChart3 size={28} className="inline mr-2" style={{ color: '#a855f7' }} />
          Compare<span className="gradient-text"> Plants</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Benchmark locations side-by-side. Green marks the better value.</p>
      </div>

      {/* Plant picker */}
      <div className="flex flex-wrap gap-2 mb-6">
        {plants.map(p => {
          const on = selected.includes(p.plant_id);
          return (
            <button
              key={p.plant_id}
              onClick={() => toggle(p.plant_id)}
              className="px-4 py-2 rounded-xl text-sm font-medium transition-all"
              style={{
                background: on ? 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(6,182,212,0.12))' : 'rgba(255,255,255,0.03)',
                border: `1px solid ${on ? 'var(--border-active)' : 'var(--border)'}`,
                color: on ? 'var(--text-primary)' : 'var(--text-secondary)',
              }}
            >
              {p.name}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)' }}>
          <Loader2 size={16} className="animate-spin" /> Loading comparison…
        </div>
      ) : rows.length === 0 ? (
        <p style={{ color: 'var(--text-muted)' }}>Select at least one plant to compare.</p>
      ) : (
        <div className="industrial-card p-0 overflow-x-auto animate-fade-in-up">
          <table className="w-full text-sm" style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th className="text-left p-4" style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>Metric</th>
                {rows.map(m => (
                  <th key={m.plant_id} className="text-center p-4" style={{ color: 'var(--text-primary)', borderBottom: '1px solid var(--border)' }}>
                    {m.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map(r => {
                const best = bestFor(r);
                return (
                  <tr key={r.label}>
                    <td className="p-4" style={{ color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)' }}>{r.label}</td>
                    {rows.map(m => {
                      const v = r.get(m);
                      const isBest = best !== null && v === best;
                      return (
                        <td key={m.plant_id} className="text-center p-4 font-semibold" style={{
                          color: isBest ? '#22c55e' : 'var(--text-primary)',
                          borderBottom: '1px solid var(--border)',
                        }}>
                          {v}{isBest ? ' ★' : ''}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
