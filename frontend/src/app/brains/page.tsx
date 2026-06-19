'use client';
import { useEffect, useState } from 'react';
import { useSureflowStore } from '@/lib/store';
import { Brain, Cpu, Shield, TrendingUp, Clock, ChevronDown, ChevronUp, RefreshCw, Zap } from 'lucide-react';

const BRAIN_META: Record<string, {
  color: string;
  gradient: string;
  role: string;
  description: string;
  capabilities: string[];
  philosophy: string;
}> = {
  CEO: {
    color: '#6366f1',
    gradient: 'linear-gradient(135deg, #6366f1, #4f46e5)',
    role: 'Executive Orchestrator',
    description: 'Strategic reasoning engine that combines executive thinking styles of Nadella, Huang, Musk, and Ravikant.',
    capabilities: ['Strategic goal decomposition', 'Department orchestration', 'KPI monitoring', 'Conflict resolution', 'Resource allocation', 'Revenue planning'],
    philosophy: 'Would I make this decision if this was my own company?',
  },
  CMO: {
    color: '#06b6d4',
    gradient: 'linear-gradient(135deg, #06b6d4, #0284c7)',
    role: 'Content & Marketing',
    description: 'Platform-native content strategist with deep expertise in virality mechanics, buyer psychology, and storytelling.',
    capabilities: ['30-day content calendar', 'Reel scripts with exact shots', 'Hook generation', 'Image prompt creation', 'Platform optimization', 'Cultural moment awareness'],
    philosophy: 'Would I personally share this? Would it stop my scroll?',
  },
  RESEARCH: {
    color: '#f59e0b',
    gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
    role: 'Market Intelligence',
    description: 'McKinsey-depth research analyst capable of competitive intelligence, SWOT generation, and trend analysis with confidence scoring.',
    capabilities: ['Competitor intelligence', 'SWOT generation', 'Trend analysis', 'Audience discovery', 'Sentiment analysis', 'Risk estimation'],
    philosophy: 'What would a CFO challenge in this analysis?',
  },
  SDR: {
    color: '#10b981',
    gradient: 'linear-gradient(135deg, #10b981, #059669)',
    role: 'Lead Qualification',
    description: 'Elite sales development brain that can REJECT poor leads, qualify relentlessly, and draft hyper-personalized outreach.',
    capabilities: ['ICP scoring (5 dimensions)', 'Lead rejection authority', 'Objection anticipation', 'Follow-up sequences', 'Meeting booking', 'Buying stage identification'],
    philosophy: 'Would I genuinely chase this lead?',
  },
  AE: {
    color: '#ec4899',
    gradient: 'linear-gradient(135deg, #ec4899, #db2777)',
    role: 'Deal Closing',
    description: 'Senior account executive brain with stakeholder mapping, pricing strategy, and probability-weighted revenue forecasting.',
    capabilities: ['Stakeholder mapping', 'Proposal structuring', 'Pricing recommendations', 'Revenue forecasting', 'Objection handling', 'Upsell identification'],
    philosophy: 'What could kill this deal? Be honest.',
  },
  RISK: {
    color: '#ef4444',
    gradient: 'linear-gradient(135deg, #ef4444, #dc2626)',
    role: 'Risk & Veto Authority',
    description: 'Chief Risk Officer brain with veto power over any campaign. Predicts failure probability and estimates financial impact.',
    capabilities: ['Campaign failure prediction', 'Audience mismatch analysis', 'Brand dilution risk', 'Financial impact estimation', 'Veto authority (>70% failure)', 'Recovery planning'],
    philosophy: 'I am not a pessimist. I am a realist who enables bold action.',
  },
  EMAIL: {
    color: '#8b5cf6',
    gradient: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
    role: 'Outreach & Nurture',
    description: 'Email marketing specialist that generates A/B variants, predicts open rates, and builds full follow-up sequences.',
    capabilities: ['A/B variant generation', 'Open rate prediction', 'Reply probability scoring', 'Spam risk assessment', 'Follow-up sequences', 'Tone adaptation'],
    philosophy: 'Would a busy exec actually reply to this?',
  },
  ANALYST: {
    color: '#fb923c',
    gradient: 'linear-gradient(135deg, #fb923c, #ea580c)',
    role: 'KPI & Analytics',
    description: 'Business intelligence brain that tracks engagement metrics, revenue trends, and campaign performance.',
    capabilities: ['KPI monitoring', 'Revenue tracking', 'Engagement analytics', 'Trend detection', 'Performance benchmarking', 'Reporting'],
    philosophy: 'What data would change this decision?',
  },
};

function ConfidenceBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="w-full h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.05)' }}>
      <div
        className="h-1.5 rounded-full transition-all duration-700"
        style={{ width: `${value}%`, background: color }}
      />
    </div>
  );
}

function BrainCard({ agent }: { agent: any }) {
  const [expanded, setExpanded] = useState(false);
  const [memory, setMemory] = useState<any>(null);
  const meta = BRAIN_META[agent.id] || BRAIN_META['ANALYST'];
  const isActive = agent.status === 'working';

  const loadMemory = async () => {
    if (memory) { setExpanded(e => !e); return; }
    try {
      const res = await fetch(`http://localhost:8000/api/v1/memory/${agent.id}`);
      if (res.ok) setMemory(await res.json());
    } catch {}
    setExpanded(true);
  };

  return (
    <div
      className="glass-card p-5 animate-fade-in-up transition-all duration-200"
      style={{
        borderColor: isActive ? meta.color : 'var(--border)',
        boxShadow: isActive ? `0 0 24px ${meta.color}33` : undefined,
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: meta.gradient }}
          >
            <Brain size={18} color="white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>{agent.id} Brain</span>
              {isActive && <div className="status-dot-working" />}
            </div>
            <div className="text-xs" style={{ color: meta.color }}>{meta.role}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs font-mono px-2 py-1 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)' }}>
            {agent.model}
          </div>
        </div>
      </div>

      {/* Description */}
      <p className="text-xs mb-4" style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
        {meta.description}
      </p>

      {/* Capabilities */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {meta.capabilities.slice(0, 3).map(cap => (
          <span
            key={cap}
            className="text-[10px] px-2 py-0.5 rounded-full"
            style={{ background: `${meta.color}15`, color: meta.color, border: `1px solid ${meta.color}30` }}
          >
            {cap}
          </span>
        ))}
        {meta.capabilities.length > 3 && (
          <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)' }}>
            +{meta.capabilities.length - 3} more
          </span>
        )}
      </div>

      {/* Philosophy */}
      <div className="p-3 rounded-xl mb-4" style={{ background: `${meta.color}08`, border: `1px solid ${meta.color}15` }}>
        <p className="text-[10px] italic" style={{ color: 'var(--text-muted)' }}>
          &ldquo;{meta.philosophy}&rdquo;
        </p>
      </div>

      {/* Expand button */}
      <button
        onClick={loadMemory}
        className="w-full flex items-center justify-between text-xs py-2 px-3 rounded-xl transition-all"
        style={{ background: 'rgba(255,255,255,0.03)', color: 'var(--text-muted)' }}
      >
        <span>Memory & Episodes</span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {/* Memory Panel */}
      {expanded && memory && (
        <div className="mt-3 space-y-2 animate-fade-in-up">
          <div className="flex gap-4">
            <div className="text-center">
              <div className="text-lg font-bold" style={{ color: meta.color }}>{memory.episodic_count}</div>
              <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Episodes</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold" style={{ color: '#f59e0b' }}>{memory.reflection_count}</div>
              <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Reflections</div>
            </div>
          </div>
          {memory.recent_episodes?.length > 0 && (
            <div>
              <div className="text-[10px] uppercase tracking-widest mb-1" style={{ color: 'var(--text-muted)' }}>Recent Episodes</div>
              {memory.recent_episodes.map((ep: any, i: number) => (
                <div key={i} className="text-[10px] py-1 border-b" style={{ color: 'var(--text-secondary)', borderColor: 'var(--border)' }}>
                  {ep.output_summary?.slice(0, 80)}...
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function BrainsPage() {
  const { agents, fetchAgents } = useSureflowStore();

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const workingCount = agents.filter(a => a.status === 'working').length;

  return (
    <div className="p-6" style={{ background: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
            <span className="gradient-text">Brain</span> Roster
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            Your autonomous digital executive team — each brain thinks, reasons, and self-challenges before acting.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {workingCount > 0 && (
            <div className="flex items-center gap-2 px-4 py-2 rounded-xl" style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)' }}>
              <div className="status-dot-working" />
              <span className="text-sm font-medium" style={{ color: '#818cf8' }}>
                {workingCount} brain{workingCount > 1 ? 's' : ''} active
              </span>
            </div>
          )}
          <button
            onClick={fetchAgents}
            className="btn-ghost"
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* V2 Philosophy Banner */}
      <div className="glass-card p-5 mb-8" style={{ borderColor: 'rgba(99,102,241,0.3)', background: 'rgba(99,102,241,0.05)' }}>
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(135deg, #6366f1, #06b6d4)' }}>
            <Zap size={18} color="white" />
          </div>
          <div>
            <div className="font-bold mb-1" style={{ color: 'var(--text-primary)' }}>CompanyOS V2 — Autonomous Business Intelligence</div>
            <p className="text-sm" style={{ color: 'var(--text-secondary)', lineHeight: '1.7' }}>
              Every brain is a senior professional with 15+ years of domain expertise. They don&apos;t answer prompts —
              they <strong style={{ color: '#818cf8' }}>reason</strong>, challenge themselves, check their confidence,
              estimate risk, and apply the company constitution before producing any output.
              The Risk Brain can <strong style={{ color: '#ef4444' }}>veto</strong> any campaign.
              The Debate Engine resolves conflicts. The CEO synthesizes everything.
            </p>
          </div>
        </div>
      </div>

      {/* Brain Grid */}
      {agents.length === 0 ? (
        <div className="text-center py-20">
          <Brain size={40} className="mx-auto mb-4 opacity-30" style={{ color: 'var(--text-muted)' }} />
          <div style={{ color: 'var(--text-muted)' }}>Connecting to backend...</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
          {agents.map(agent => (
            <BrainCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}

      {/* Decision Framework Reference */}
      <div className="mt-10 glass-card p-6">
        <h2 className="text-lg font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
          V2 Decision Framework — Applied by Every Brain
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { icon: '🧠', label: 'Internal Reasoning', desc: 'Full chain-of-thought before output' },
            { icon: '🔄', label: 'Alternatives Considered', desc: 'Multiple approaches evaluated' },
            { icon: '📊', label: 'Confidence Score', desc: '0–100 certainty rating per output' },
            { icon: '📈', label: 'Expected ROI', desc: 'Financial or engagement estimate' },
            { icon: '⚠️', label: 'Risk Estimation', desc: 'low / medium / high / critical' },
            { icon: '🏛️', label: 'Constitution Check', desc: 'Brand & legal compliance validation' },
          ].map(({ icon, label, desc }) => (
            <div key={label} className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)' }}>
              <div className="text-xl mb-1">{icon}</div>
              <div className="text-sm font-medium mb-0.5" style={{ color: 'var(--text-primary)' }}>{label}</div>
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
