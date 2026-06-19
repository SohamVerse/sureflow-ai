'use client';
import { useEffect, useState } from 'react';
import { useSureflowStore } from '@/lib/store';
import type { Lead, LeadStatus } from '@/types';
import { Star, Zap, Plus, X } from 'lucide-react';

const COLUMNS: { key: LeadStatus; label: string }[] = [
  { key: 'new',         label: 'New' },
  { key: 'in_sequence', label: 'In Sequence' },
  { key: 'booked',      label: 'Booked' },
  { key: 'closed',      label: 'Closed' },
];

function IcpScore({ score }: { score: number }) {
  const color = score >= 8 ? '#10b981' : score >= 5 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-1">
      <Star size={10} style={{ color, fill: color }} />
      <span className="text-xs font-bold" style={{ color }}>{score.toFixed(1)}</span>
    </div>
  );
}

function LeadCard({ lead, onScore, onMove }: {
  lead: Lead;
  onScore: () => void;
  onMove: (status: LeadStatus) => void;
}) {
  return (
    <div id={`lead-card-${lead.id}`} className="glass-card glass-card-hover p-4 mb-3">
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{lead.name}</p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{lead.title}</p>
          <p className="text-xs font-medium" style={{ color: '#818cf8' }}>{lead.company}</p>
        </div>
        <IcpScore score={lead.icp_score} />
      </div>
      <div className="flex flex-wrap gap-1.5 mb-3">
        <span className="badge badge-pending" style={{ fontSize: '9px' }}>{lead.buying_stage}</span>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
          {lead.touchpoints} touchpoint{lead.touchpoints !== 1 ? 's' : ''}
        </span>
      </div>
      <div className="flex gap-1.5">
        <button
          id={`score-lead-${lead.id}`}
          onClick={onScore}
          className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs flex-1 justify-center"
          style={{ background: 'rgba(99,102,241,0.1)', color: '#818cf8', border: '1px solid rgba(99,102,241,0.2)' }}
        >
          <Zap size={10} /> Score
        </button>
        {lead.status === 'new' && (
          <button
            id={`sequence-lead-${lead.id}`}
            onClick={() => onMove('in_sequence')}
            className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs flex-1 justify-center"
            style={{ background: 'rgba(6,182,212,0.1)', color: '#06b6d4', border: '1px solid rgba(6,182,212,0.2)' }}
          >
            → Sequence
          </button>
        )}
        {lead.status === 'in_sequence' && (
          <button
            id={`book-lead-${lead.id}`}
            onClick={() => onMove('booked')}
            className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs flex-1 justify-center"
            style={{ background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.2)' }}
          >
            → Book
          </button>
        )}
      </div>
    </div>
  );
}

function AddLeadModal({ onClose, onCreate }: { onClose: () => void; onCreate: (d: Partial<Lead>) => void }) {
  const [form, setForm] = useState({ name: '', email: '', company: '', title: '' });
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.7)' }}>
      <div className="glass-card p-6 w-96">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Add New Lead</h3>
          <button onClick={onClose}><X size={18} style={{ color: 'var(--text-muted)' }} /></button>
        </div>
        {(['name', 'email', 'company', 'title'] as const).map(field => (
          <input
            key={field}
            id={`lead-${field}-input`}
            placeholder={field.charAt(0).toUpperCase() + field.slice(1)}
            value={form[field]}
            onChange={e => setForm(prev => ({ ...prev, [field]: e.target.value }))}
            className="w-full px-4 py-2.5 rounded-xl text-sm mb-3 outline-none"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
          />
        ))}
        <button
          id="create-lead-submit"
          className="btn-primary w-full justify-center"
          onClick={() => { onCreate(form); onClose(); }}
        >
          Add Lead
        </button>
      </div>
    </div>
  );
}

export default function LeadPipeline() {
  const { leads, fetchLeads, createLead, updateLead, scoreLead } = useSureflowStore();
  const [showAdd, setShowAdd] = useState(false);

  useEffect(() => { fetchLeads(); }, [fetchLeads]);

  const byStatus = (status: LeadStatus) => leads.filter(l => l.status === status);

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
            Lead <span className="gradient-text">Pipeline</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Qualified prospects for custom Web & SaaS app development</p>
        </div>
        <button id="add-lead-btn" className="btn-primary" onClick={() => setShowAdd(true)}>
          <Plus size={14} /> Add Lead
        </button>
      </div>

      {showAdd && (
        <AddLeadModal
          onClose={() => setShowAdd(false)}
          onCreate={(data) => createLead(data)}
        />
      )}

      <div className="flex gap-5 overflow-x-auto pb-4">
        {COLUMNS.map(col => {
          const items = byStatus(col.key);
          return (
            <div key={col.key} className="kanban-col flex-shrink-0" style={{ width: 300 }}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                  {col.label}
                </h3>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--text-muted)' }}>
                  {items.length}
                </span>
              </div>
              <div>
                {items.length === 0 ? (
                  <div className="text-center py-8 text-xs" style={{ color: 'var(--text-muted)' }}>No leads</div>
                ) : (
                  items.map(lead => (
                    <LeadCard
                      key={lead.id}
                      lead={lead}
                      onScore={() => scoreLead(lead.id)}
                      onMove={(status) => updateLead(lead.id, { status })}
                    />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
