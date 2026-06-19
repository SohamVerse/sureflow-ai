'use client';
import { useEffect, useState } from 'react';
import { useSureflowStore } from '@/lib/store';
import {
  ShieldCheck, AlertTriangle, CheckCircle, XCircle,
  ChevronDown, ChevronUp, Brain, RefreshCw, AlertOctagon,
  TrendingDown, Eye
} from 'lucide-react';

const RISK_COLORS: Record<string, string> = {
  low: '#10b981',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#dc2626',
};

const TIER_COLORS: Record<string, string> = {
  AUTO_APPROVE: '#10b981',
  MANAGER_APPROVAL: '#f59e0b',
  CEO_APPROVAL: '#ef4444',
};

const STATUS_BADGE: Record<string, { bg: string; color: string; label: string }> = {
  pending: { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b', label: 'Pending Review' },
  vetoed: { bg: 'rgba(239,68,68,0.15)', color: '#ef4444', label: 'Risk Vetoed' },
};

function ConfidenceRing({ score, color }: { score: number; color: string }) {
  const r = 24;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - score / 100);
  return (
    <svg width="60" height="60" viewBox="0 0 60 60">
      <circle cx="30" cy="30" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
      <circle
        cx="30" cy="30" r={r} fill="none" stroke={color} strokeWidth="4"
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%', transition: 'stroke-dashoffset 0.8s ease' }}
      />
      <text x="30" y="35" textAnchor="middle" fontSize="11" fontWeight="700" fill={color}>{score}%</text>
    </svg>
  );
}

function ApprovalCard({ item, onApprove, onReject }: { item: any; onApprove: () => void; onReject: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const riskColor = RISK_COLORS[item.risk_level] || '#f59e0b';
  const tierColor = TIER_COLORS[item.approval_tier] || '#f59e0b';
  const statusMeta = STATUS_BADGE[item.status] || STATUS_BADGE['pending'];
  const isVetoed = item.status === 'vetoed';

  return (
    <div
      className="glass-card p-5 animate-fade-in-up"
      style={{
        borderColor: isVetoed ? 'rgba(239,68,68,0.4)' : 'var(--border)',
        boxShadow: isVetoed ? '0 0 24px rgba(239,68,68,0.1)' : undefined,
      }}
    >
      {/* Top Row */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(255,255,255,0.05)' }}
          >
            {isVetoed ? <AlertOctagon size={16} color="#ef4444" /> : <AlertTriangle size={16} color="#f59e0b" />}
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm mb-1 truncate" style={{ color: 'var(--text-primary)' }}>
              {item.title}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="badge text-[10px] px-2 py-0.5 rounded-full" style={{ background: statusMeta.bg, color: statusMeta.color }}>
                {statusMeta.label}
              </span>
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                {item.agent_type} · {item.platform}
              </span>
            </div>
          </div>
        </div>

        {/* Confidence Ring */}
        {item.confidence != null && (
          <ConfidenceRing score={item.confidence} color={riskColor} />
        )}
      </div>

      {/* Risk + Tier Badges */}
      <div className="flex items-center gap-2 mb-3">
        {item.risk_level && (
          <span
            className="text-[10px] px-2 py-0.5 rounded-full font-semibold"
            style={{ background: `${riskColor}15`, color: riskColor, border: `1px solid ${riskColor}30` }}
          >
            {item.risk_level?.toUpperCase()} RISK
          </span>
        )}
        {item.approval_tier && (
          <span
            className="text-[10px] px-2 py-0.5 rounded-full font-semibold"
            style={{ background: `${tierColor}15`, color: tierColor, border: `1px solid ${tierColor}30` }}
          >
            {item.approval_tier?.replace('_', ' ')}
          </span>
        )}
        {item.risk_score != null && (
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            Failure prob: <strong style={{ color: riskColor }}>{item.risk_score}%</strong>
          </span>
        )}
      </div>

      {/* Constitution Violations */}
      {item.constitution_violations?.length > 0 && (
        <div className="mb-3 p-2.5 rounded-lg" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
          <div className="text-[10px] font-semibold mb-1 uppercase" style={{ color: '#ef4444' }}>
            ⚠️ Constitution Violations
          </div>
          {item.constitution_violations.map((v: string, i: number) => (
            <div key={i} className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>{v}</div>
          ))}
        </div>
      )}

      {/* Debate Log */}
      {item.debate_log?.length > 0 && (
        <div className="mb-3 p-2.5 rounded-lg" style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)' }}>
          <div className="text-[10px] font-semibold mb-1 uppercase" style={{ color: '#f59e0b' }}>
            ⚡ Debate Engine Notes
          </div>
          {item.debate_log.map((d: string, i: number) => (
            <div key={i} className="text-[10px]" style={{ color: 'var(--text-secondary)' }}>{d}</div>
          ))}
        </div>
      )}

      {/* Expandable Reasoning */}
      {item.reasoning && (
        <>
          <button
            onClick={() => setExpanded(e => !e)}
            className="w-full flex items-center justify-between text-xs py-2 px-3 rounded-xl transition-all mb-3"
            style={{ background: 'rgba(255,255,255,0.03)', color: 'var(--text-muted)' }}
          >
            <span className="flex items-center gap-1"><Eye size={12} /> Agent Reasoning</span>
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          {expanded && (
            <div className="mb-3 p-3 rounded-xl text-xs animate-fade-in-up" style={{ background: 'rgba(255,255,255,0.02)', color: 'var(--text-secondary)', lineHeight: '1.7' }}>
              {item.reasoning}
            </div>
          )}
        </>
      )}

      {/* Actions */}
      <div className="flex gap-2 mt-2">
        <button
          id={`approve-${item.id}`}
          onClick={onApprove}
          className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-sm font-semibold transition-all"
          style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981', border: '1px solid rgba(16,185,129,0.3)' }}
        >
          <CheckCircle size={14} /> Approve
        </button>
        <button
          id={`reject-${item.id}`}
          onClick={onReject}
          className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-sm font-semibold transition-all"
          style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }}
        >
          <XCircle size={14} /> Reject
        </button>
      </div>
    </div>
  );
}

export default function ApprovalsPage() {
  const { approvalItems, pendingApprovals, fetchPendingApprovals, approveItem, rejectItem } = useSureflowStore();
  const [filter, setFilter] = useState<'all' | 'vetoed' | 'pending'>('all');

  useEffect(() => {
    fetchPendingApprovals();
  }, [fetchPendingApprovals]);

  const filtered = approvalItems.filter(item => {
    if (filter === 'vetoed') return item.status === 'vetoed';
    if (filter === 'pending') return item.status === 'pending';
    return true;
  });

  const vetoedCount = approvalItems.filter(i => i.status === 'vetoed').length;

  return (
    <div className="p-6" style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
            <span className="gradient-text">Approval</span> Center
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            Human-in-the-loop decision authority for high-risk and vetoed actions.
          </p>
        </div>
        <button onClick={fetchPendingApprovals} className="btn-ghost">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="glass-card p-4 text-center">
          <div className="text-2xl font-bold" style={{ color: '#f59e0b' }}>{pendingApprovals}</div>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Awaiting Decision</div>
        </div>
        <div className="glass-card p-4 text-center">
          <div className="text-2xl font-bold" style={{ color: '#ef4444' }}>{vetoedCount}</div>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Risk Vetoed</div>
        </div>
        <div className="glass-card p-4 text-center">
          <div className="text-2xl font-bold" style={{ color: '#10b981' }}>
            {approvalItems.filter(i => i.approval_tier === 'CEO_APPROVAL').length}
          </div>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>CEO Approval Required</div>
        </div>
      </div>

      {/* Approval Tiers Explanation */}
      <div className="glass-card p-4 mb-6">
        <div className="flex items-center gap-6">
          {[
            { tier: 'LOW RISK', desc: 'Auto-approved by system', color: '#10b981' },
            { tier: 'MEDIUM RISK', desc: 'Manager approval required', color: '#f59e0b' },
            { tier: 'HIGH / VETOED', desc: 'CEO approval required', color: '#ef4444' },
          ].map(({ tier, desc, color }) => (
            <div key={tier} className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full" style={{ background: color }} />
              <div>
                <div className="text-xs font-semibold" style={{ color }}>{tier}</div>
                <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-5">
        {[
          { key: 'all', label: `All (${approvalItems.length})` },
          { key: 'vetoed', label: `Risk Vetoed (${vetoedCount})` },
          { key: 'pending', label: `Pending (${approvalItems.length - vetoedCount})` },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key as any)}
            className="px-4 py-2 rounded-xl text-sm font-medium transition-all"
            style={{
              background: filter === key ? 'linear-gradient(135deg, #6366f1, #4f46e5)' : 'rgba(255,255,255,0.04)',
              color: filter === key ? 'white' : 'var(--text-muted)',
              border: filter === key ? 'none' : '1px solid var(--border)',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Items Grid */}
      {filtered.length === 0 ? (
        <div className="text-center py-24">
          <ShieldCheck size={48} className="mx-auto mb-4 opacity-20" style={{ color: '#10b981' }} />
          <div className="text-lg font-semibold mb-2" style={{ color: 'var(--text-secondary)' }}>
            All Clear
          </div>
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>
            No items requiring your attention right now.
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(item => (
            <ApprovalCard
              key={item.id}
              item={item}
              onApprove={() => approveItem(item.id)}
              onReject={() => rejectItem(item.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
