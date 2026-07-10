'use client';
import { useState } from 'react';
import { Brain, ChevronDown, ShieldAlert, Lightbulb } from 'lucide-react';
import type { AgentReasoning } from '@/types';

interface AgentReasoningPanelProps {
  data: AgentReasoning;
  sourcesConsulted?: string[];
  safetyAlerts?: string[];
  followUpQuestions?: string[];
  onFollowUpClick?: (question: string) => void;
  defaultOpen?: boolean;
}

const RISK_COLORS: Record<string, string> = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#dc2626',
};

/**
 * Surfaces the reasoning/confidence/risk/self-challenge fields every agent
 * already returns via the shared BaseBrain contract (backend/core/brain.py),
 * but which the UI previously discarded.
 */
export function AgentReasoningPanel({
  data,
  sourcesConsulted,
  safetyAlerts,
  followUpQuestions,
  onFollowUpClick,
  defaultOpen = false,
}: AgentReasoningPanelProps) {
  const [open, setOpen] = useState(defaultOpen);

  const hasReasoning = Boolean(data.reasoning || data.self_challenge || data.alternatives?.length);
  const hasExtras = Boolean(sourcesConsulted?.length || safetyAlerts?.length || followUpQuestions?.length);
  if (!hasReasoning && !hasExtras) return null;

  return (
    <div className="mt-3 rounded-xl overflow-hidden" style={{ border: '1px solid var(--border)', background: 'rgba(255,255,255,0.02)' }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold cursor-pointer"
        style={{ color: 'var(--text-muted)' }}
      >
        <span className="flex items-center gap-2 flex-wrap">
          <Brain size={13} style={{ color: '#818cf8' }} />
          AI Reasoning
          {data.risk_level && (
            <span
              className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase"
              style={{
                background: `${RISK_COLORS[data.risk_level] || '#6366f1'}22`,
                color: RISK_COLORS[data.risk_level] || '#818cf8',
              }}
            >
              {data.risk_level} risk
            </span>
          )}
          {typeof data.confidence === 'number' && (
            <span className="text-[10px] font-normal" style={{ color: 'var(--text-muted)' }}>
              {Math.round(data.confidence)}% confidence
            </span>
          )}
        </span>
        <ChevronDown size={14} style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s', flexShrink: 0 }} />
      </button>

      {open && (
        <div className="px-3 pb-3 space-y-3">
          {data.reasoning && (
            <div>
              <div className="text-[10px] font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>Chain of thought</div>
              <p className="text-xs" style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>{data.reasoning}</p>
            </div>
          )}

          {sourcesConsulted && sourcesConsulted.length > 0 && (
            <div>
              <div className="text-[10px] font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>Sources consulted</div>
              <div className="flex flex-wrap gap-1.5">
                {sourcesConsulted.map((s, i) => (
                  <span key={i} className="citation-card">{s}</span>
                ))}
              </div>
            </div>
          )}

          {data.alternatives && data.alternatives.length > 0 && (
            <div>
              <div className="text-[10px] font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>Alternatives considered</div>
              <ul className="space-y-1">
                {data.alternatives.map((a, i) => (
                  <li key={i} className="text-xs flex gap-1.5" style={{ color: 'var(--text-secondary)' }}>
                    <span style={{ color: '#818cf8' }}>•</span>{a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.self_challenge && (
            <div>
              <div className="text-[10px] font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>Self-challenge</div>
              <p className="text-xs italic" style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>{data.self_challenge}</p>
            </div>
          )}

          {safetyAlerts && safetyAlerts.length > 0 && (
            <div>
              <div className="text-[10px] font-semibold mb-1 flex items-center gap-1" style={{ color: '#ef4444' }}>
                <ShieldAlert size={11} /> Safety alerts
              </div>
              <ul className="space-y-1">
                {safetyAlerts.map((s, i) => (
                  <li key={i} className="text-xs" style={{ color: '#ef4444' }}>{s}</li>
                ))}
              </ul>
            </div>
          )}

          {followUpQuestions && followUpQuestions.length > 0 && (
            <div>
              <div className="text-[10px] font-semibold mb-1 flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
                <Lightbulb size={11} /> Follow-up questions
              </div>
              <div className="flex flex-wrap gap-2">
                {followUpQuestions.map((q, i) => (
                  <button key={i} onClick={() => onFollowUpClick?.(q)} className="suggested-prompt">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
