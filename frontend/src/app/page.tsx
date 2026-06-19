'use client';
import { useEffect, useState } from 'react';
import { useSureflowStore } from '@/lib/store';
import { Zap, TrendingUp, Users, Phone, Clock, ChevronRight, Play, CheckCircle, XCircle } from 'lucide-react';

export default function CommandCenter() {
  const { kpis, pipelineItems, fetchKPIs, fetchPipelineItems, updateItemStatus, runPipeline, pipelineRunning } = useSureflowStore();
  const [goal, setGoal] = useState('');

  useEffect(() => {
    fetchKPIs();
    fetchPipelineItems('pending');
  }, [fetchKPIs, fetchPipelineItems]);

  const pending = pipelineItems.filter(i => i.status === 'pending');

  const kpiCards = [
    { label: 'Posts This Week',   value: kpis?.posts_this_week  ?? 0, icon: TrendingUp, color: '#6366f1', glow: 'rgba(99,102,241,0.2)' },
    { label: 'Active Leads',      value: kpis?.active_leads     ?? 0, icon: Users,      color: '#06b6d4', glow: 'rgba(6,182,212,0.2)' },
    { label: 'Calls Booked',      value: kpis?.calls_booked     ?? 0, icon: Phone,      color: '#10b981', glow: 'rgba(16,185,129,0.2)' },
    { label: 'Needs Review',      value: kpis?.pending_review   ?? 0, icon: Clock,      color: '#f59e0b', glow: 'rgba(245,158,11,0.2)' },
  ];

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          Company<span className="gradient-text">OS</span> Command Center
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Autonomous intelligence orchestration and business operation monitoring.</p>
      </div>

      {/* Run Pipeline */}
      <div className="glass-card p-6 mb-8 animate-fade-in-up" style={{ animationDelay: '0.05s' }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.15)' }}>
            <Zap size={16} style={{ color: '#6366f1' }} />
          </div>
          <h2 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Trigger Agent Pipeline</h2>
        </div>
        <div className="flex gap-3">
          <input
            id="pipeline-goal-input"
            type="text"
            value={goal}
            onChange={e => setGoal(e.target.value)}
            placeholder="e.g. Analyze recent LMS trends on LinkedIn to generate a new feature awareness post..."
            className="flex-1 px-4 py-3 rounded-xl text-sm outline-none transition-all"
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
            }}
            onKeyDown={e => { if (e.key === 'Enter' && goal.trim()) { runPipeline(goal); setGoal(''); } }}
          />
          <button
            id="run-pipeline-btn"
            className="btn-primary"
            disabled={pipelineRunning || !goal.trim()}
            onClick={() => { if (goal.trim()) { runPipeline(goal); setGoal(''); } }}
          >
            {pipelineRunning ? (
              <span className="flex items-center gap-2">
                <div className="status-dot-working" />
                Orchestrating...
              </span>
            ) : (
              <><Play size={14} /> Run Pipeline</>
            )}
          </button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-4 gap-4 mb-8" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        {kpiCards.map((card, i) => (
          <div
            key={card.label}
            className="glass-card glass-card-hover p-6 animate-fade-in-up"
            style={{ animationDelay: `${0.1 + i * 0.05}s` }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `rgba(${card.color === '#6366f1' ? '99,102,241' : card.color === '#06b6d4' ? '6,182,212' : card.color === '#10b981' ? '16,185,129' : '245,158,11'},0.15)` }}>
                <card.icon size={18} style={{ color: card.color }} />
              </div>
            </div>
            <div className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
              {card.value.toLocaleString()}
            </div>
            <div className="text-sm" style={{ color: 'var(--text-muted)' }}>{card.label}</div>
          </div>
        ))}
      </div>

      {/* Two Column Layout: Needs Review & Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Needs Review Queue */}
        <div className="glass-card p-6 animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-semibold text-lg" style={{ color: 'var(--text-primary)' }}>
              Approval Center
              {pending.length > 0 && (
                <span className="ml-2 badge badge-pending">{pending.length}</span>
              )}
            </h2>
            <a href="/approvals" className="flex items-center gap-1 text-sm" style={{ color: '#6366f1' }}>
              View Approvals <ChevronRight size={14} />
            </a>
          </div>

          {pending.length === 0 ? (
            <div className="text-center py-12" style={{ color: 'var(--text-muted)' }}>
              <CheckCircle size={40} className="mx-auto mb-3 opacity-30" />
              <p>All clear. No decisions pending.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {pending.slice(0, 5).map(item => (
                <div
                  key={item.id}
                  className="flex flex-col gap-2 p-4 rounded-xl transition-all"
                  style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="badge badge-pending">{item.agent_type}</span>
                      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{item.platform}</span>
                    </div>
                    {item.confidence && (
                      <span className="text-xs font-mono" style={{ color: '#f59e0b' }}>
                        Conf: {item.confidence}%
                      </span>
                    )}
                  </div>
                  <p className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                    {item.title}
                  </p>
                  <div className="flex gap-2 mt-2">
                    <button
                      onClick={() => updateItemStatus(item.id, 'approved')}
                      className="flex-1 py-1.5 rounded-lg text-xs font-medium transition-all"
                      style={{ background: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.3)' }}
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => updateItemStatus(item.id, 'rejected')}
                      className="flex-1 py-1.5 rounded-lg text-xs font-medium transition-all"
                      style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }}
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live Activity Feed */}
        <div className="glass-card p-6 animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-semibold text-lg flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Live Activity
            </h2>
          </div>
          
          <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
            {/* Hardcoded sample feed for visual demo, but in real app would use activityFeed from store */}
            <div className="activity-feed-item">
              <span className="text-[10px] text-gray-500 font-mono w-12 pt-0.5">Now</span>
              <div className="flex-1">
                <span className="text-xs font-bold text-indigo-400">CEO</span>
                <span className="text-xs text-gray-300 ml-2">Initiated workflow for Q3 marketing goals.</span>
              </div>
            </div>
            <div className="activity-feed-item">
              <span className="text-[10px] text-gray-500 font-mono w-12 pt-0.5">2m ago</span>
              <div className="flex-1">
                <span className="text-xs font-bold text-amber-500">RESEARCH</span>
                <span className="text-xs text-gray-300 ml-2">Completed SWOT analysis on top 3 competitors.</span>
                <div className="mt-1 text-[10px] text-gray-400 bg-black/20 p-2 rounded">
                  Confidence: 92% | Identified key gap in competitor pricing.
                </div>
              </div>
            </div>
            <div className="activity-feed-item">
              <span className="text-[10px] text-gray-500 font-mono w-12 pt-0.5">15m ago</span>
              <div className="flex-1">
                <span className="text-xs font-bold text-red-500">RISK</span>
                <span className="text-xs text-gray-300 ml-2">Vetoed email campaign draft.</span>
                <div className="mt-1 text-[10px] text-red-400 bg-red-500/10 p-2 rounded border border-red-500/20">
                  Risk Level: HIGH. Language violates brand tone guidelines.
                </div>
              </div>
            </div>
            <div className="activity-feed-item">
              <span className="text-[10px] text-gray-500 font-mono w-12 pt-0.5">1h ago</span>
              <div className="flex-1">
                <span className="text-xs font-bold text-cyan-500">CMO</span>
                <span className="text-xs text-gray-300 ml-2">Generated 3 new LinkedIn posts.</span>
              </div>
            </div>
            <div className="activity-feed-item opacity-50">
              <span className="text-[10px] text-gray-500 font-mono w-12 pt-0.5">2h ago</span>
              <div className="flex-1">
                <span className="text-xs font-bold text-emerald-500">SDR</span>
                <span className="text-xs text-gray-300 ml-2">Rejected 14 unqualified leads.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
