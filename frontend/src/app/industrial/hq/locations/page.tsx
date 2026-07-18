'use client';
import { useEffect, useState } from 'react';
import { plantsApi } from '@/lib/api';
import { useAuth } from '@/lib/AuthContext';
import { Building2, Plus, Trash2, ShieldAlert, Loader2, CheckCircle } from 'lucide-react';

interface AreaRow { area_id: string; name: string; }

export default function LocationsPage() {
  const { user } = useAuth();
  const [plants, setPlants] = useState<any[]>([]);
  const [name, setName] = useState('');
  const [plantId, setPlantId] = useState('');
  const [location, setLocation] = useState('');
  const [areas, setAreas] = useState<AreaRow[]>([{ area_id: '', name: '' }]);
  const [mgrEmail, setMgrEmail] = useState('');
  const [mgrPass, setMgrPass] = useState('');
  const [mgrName, setMgrName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const load = () => plantsApi.list().then(d => setPlants(d.plants)).catch(() => {});
  useEffect(() => { load(); }, []);

  const setArea = (i: number, key: keyof AreaRow, val: string) =>
    setAreas(a => a.map((r, j) => j === i ? { ...r, [key]: val } : r));

  const submit = async () => {
    setError(''); setSuccess('');
    if (!name.trim()) { setError('Plant name is required.'); return; }
    setSubmitting(true);
    try {
      const payload: any = {
        plant_id: plantId.trim() || undefined,
        name: name.trim(),
        location: location.trim(),
        areas: areas.filter(a => a.area_id.trim() && a.name.trim()),
      };
      if (mgrEmail.trim() && mgrPass.trim()) {
        payload.manager = { email: mgrEmail.trim(), password: mgrPass.trim(), name: mgrName.trim() };
      }
      const res = await plantsApi.create(payload);
      setSuccess(`Created ${res.name} (${res.plant_id})${res.manager ? ` — invited ${res.manager.email}` : ''}.`);
      setName(''); setPlantId(''); setLocation(''); setAreas([{ area_id: '', name: '' }]);
      setMgrEmail(''); setMgrPass(''); setMgrName('');
      load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to create location.');
    }
    setSubmitting(false);
  };

  if (user && user.role !== 'cto') {
    return (
      <div className="p-8 min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-primary)' }}>
        <div className="text-center">
          <ShieldAlert size={40} className="mx-auto mb-3 opacity-40" style={{ color: 'var(--text-muted)' }} />
          <p style={{ color: 'var(--text-secondary)' }}>Location provisioning is available to global (CTO) accounts only.</p>
        </div>
      </div>
    );
  }

  const inputStyle = { background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', color: 'var(--text-primary)' };

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <Building2 size={28} className="inline mr-2" style={{ color: '#a855f7' }} />
          Manage<span className="gradient-text"> Locations</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Onboard a new plant and (optionally) invite its first manager.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Existing plants */}
        <div className="industrial-card p-6">
          <h2 className="font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Existing Plants ({plants.length})</h2>
          <div className="space-y-2">
            {plants.map(p => (
              <div key={p.plant_id} className="flex items-center justify-between p-3 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)' }}>
                <div>
                  <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{p.name}</div>
                  <div className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{p.plant_id} · {p.location || '—'}</div>
                </div>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{p.stats?.equipment ?? 0} eq</div>
              </div>
            ))}
          </div>
        </div>

        {/* Add form */}
        <div className="industrial-card p-6">
          <h2 className="font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <Plus size={16} style={{ color: '#22c55e' }} /> Add Location
          </h2>

          {error && <div className="mb-3 p-3 rounded-lg text-sm" style={{ background: 'rgba(239,68,68,0.08)', color: '#ef4444' }}>{error}</div>}
          {success && <div className="mb-3 p-3 rounded-lg text-sm flex items-center gap-2" style={{ background: 'rgba(34,197,94,0.08)', color: '#22c55e' }}><CheckCircle size={14} />{success}</div>}

          <div className="space-y-3">
            <input placeholder="Plant name *" value={name} onChange={e => setName(e.target.value)} className="w-full px-3 py-2.5 rounded-lg text-sm outline-none" style={inputStyle} />
            <div className="grid grid-cols-2 gap-3">
              <input placeholder="Plant ID (auto if blank)" value={plantId} onChange={e => setPlantId(e.target.value)} className="w-full px-3 py-2.5 rounded-lg text-sm outline-none" style={inputStyle} />
              <input placeholder="Location (city, country)" value={location} onChange={e => setLocation(e.target.value)} className="w-full px-3 py-2.5 rounded-lg text-sm outline-none" style={inputStyle} />
            </div>

            <div>
              <div className="text-xs font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>Areas (optional)</div>
              {areas.map((a, i) => (
                <div key={i} className="flex gap-2 mb-2">
                  <input placeholder="AREA-XXX" value={a.area_id} onChange={e => setArea(i, 'area_id', e.target.value)} className="w-1/3 px-3 py-2 rounded-lg text-sm outline-none" style={inputStyle} />
                  <input placeholder="Area name" value={a.name} onChange={e => setArea(i, 'name', e.target.value)} className="flex-1 px-3 py-2 rounded-lg text-sm outline-none" style={inputStyle} />
                  <button onClick={() => setAreas(x => x.filter((_, j) => j !== i))} className="p-2 rounded-lg" style={{ color: 'var(--text-muted)' }}><Trash2 size={14} /></button>
                </div>
              ))}
              <button onClick={() => setAreas(a => [...a, { area_id: '', name: '' }])} className="text-xs" style={{ color: '#818cf8' }}>+ Add area</button>
            </div>

            <div>
              <div className="text-xs font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>First manager (optional)</div>
              <div className="grid grid-cols-2 gap-3 mb-2">
                <input placeholder="manager@email" value={mgrEmail} onChange={e => setMgrEmail(e.target.value)} className="w-full px-3 py-2 rounded-lg text-sm outline-none" style={inputStyle} />
                <input placeholder="Manager name" value={mgrName} onChange={e => setMgrName(e.target.value)} className="w-full px-3 py-2 rounded-lg text-sm outline-none" style={inputStyle} />
              </div>
              <input placeholder="Temp password" value={mgrPass} onChange={e => setMgrPass(e.target.value)} className="w-full px-3 py-2 rounded-lg text-sm outline-none" style={inputStyle} />
            </div>

            <button onClick={submit} disabled={submitting} className="btn-primary w-full justify-center" style={{ padding: '11px' }}>
              {submitting ? <><Loader2 size={16} className="animate-spin" /> Creating…</> : <><Building2 size={16} /> Create Location</>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
