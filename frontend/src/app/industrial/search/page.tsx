'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { systemApi } from '@/lib/api';
import { Search, Cpu, AlertTriangle, FileText, Lightbulb, Loader2 } from 'lucide-react';

function SearchResults() {
  const params = useSearchParams();
  const q = params.get('q') || '';
  const [res, setRes] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!q.trim()) { setRes(null); return; }
    setLoading(true);
    systemApi.search(q).then(d => { setRes(d); setLoading(false); }).catch(() => setLoading(false));
  }, [q]);

  const total = res ? res.equipment.length + res.incidents.length + res.documents.length + res.lessons.length : 0;

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <Search size={28} className="inline mr-2" style={{ color: '#818cf8' }} />
          Search<span className="gradient-text"> {q ? `“${q}”` : ''}</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          {q ? (loading ? 'Searching…' : `${total} result${total === 1 ? '' : 's'} across equipment, incidents, documents & lessons.`) : 'Type a query in the sidebar search box.'}
        </p>
      </div>

      {loading ? (
        <div className="flex items-center gap-2" style={{ color: 'var(--text-muted)' }}><Loader2 size={16} className="animate-spin" /> Searching…</div>
      ) : res ? (
        <div className="space-y-6">
          <Group title="Equipment" icon={Cpu} color="#3b82f6" count={res.equipment.length}>
            {res.equipment.map((e: any) => (
              <Row key={e.tag} title={`${e.tag} — ${e.name}`} sub={e.area || e.asset_class} />
            ))}
          </Group>
          <Group title="Incidents" icon={AlertTriangle} color="#ef4444" count={res.incidents.length}>
            {res.incidents.map((i: any) => (
              <Row key={i.id} title={`${i.id}: ${i.title}`} sub={`${i.severity} · ${i.equipment_tag || ''}`} />
            ))}
          </Group>
          <Group title="Documents" icon={FileText} color="#a855f7" count={res.documents.length}>
            {res.documents.map((d: any, k: number) => (
              <Row key={k} title={d.source} sub={d.snippet} />
            ))}
          </Group>
          <Group title="Lessons Learned" icon={Lightbulb} color="#eab308" count={res.lessons.length}>
            {res.lessons.map((l: any, k: number) => (
              <Row key={k} title={l.lesson} sub={`${l.category} · ${l.equipment_tag || ''}`} />
            ))}
          </Group>
        </div>
      ) : null}
    </div>
  );
}

function Group({ title, icon: Icon, color, count, children }: any) {
  if (count === 0) return null;
  return (
    <div>
      <h2 className="font-semibold mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
        <Icon size={16} style={{ color }} /> {title}
        <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: `${color}1f`, color }}>{count}</span>
      </h2>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Row({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="industrial-card p-4">
      <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{title}</div>
      {sub && <div className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-muted)' }}>{sub}</div>}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="p-8" style={{ color: 'var(--text-muted)' }}>Loading…</div>}>
      <SearchResults />
    </Suspense>
  );
}
