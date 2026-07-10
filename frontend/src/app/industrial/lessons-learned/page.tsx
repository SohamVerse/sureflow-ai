'use client';
import { useEffect, useState } from 'react';
import { useSureflowStore } from '@/lib/store';
import { industrialApi } from '@/lib/api';
import type { LessonsLearnedResult } from '@/types';
import { AgentReasoningPanel } from '@/components/industrial/AgentReasoningPanel';
import {
  Lightbulb, AlertTriangle, Loader2, ChevronDown, Play,
  TrendingUp, TrendingDown, Minus, ShieldAlert,
} from 'lucide-react';

const RISK_BADGE: Record<string, string> = {
  critical: 'critical',
  high: 'warning',
  medium: 'operational',
  low: 'operational',
};

const TREND_ICON: Record<string, typeof TrendingUp> = {
  increasing: TrendingUp,
  decreasing: TrendingDown,
  stable: Minus,
};

export default function LessonsLearnedDashboard() {
  const { industrialEquipment, fetchIndustrialEquipment } = useSureflowStore();
  const [incidentText, setIncidentText] = useState('');
  const [equipmentTag, setEquipmentTag] = useState('');
  const [incidentId, setIncidentId] = useState('');
  const [analysisScope, setAnalysisScope] = useState<'single' | 'cross_asset'>('cross_asset');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<LessonsLearnedResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchIndustrialEquipment();
  }, [fetchIndustrialEquipment]);

  const runAnalysis = async () => {
    setAnalyzing(true);
    setError('');
    setResult(null);
    try {
      const res = await industrialApi.analyzeLessons(incidentText, equipmentTag, incidentId, analysisScope);
      setResult(res);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Analysis failed';
      setError(msg);
    }
    setAnalyzing(false);
  };

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <Lightbulb size={28} className="inline mr-2" style={{ color: '#eab308' }} />
          Lessons<span className="gradient-text"> Learned</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          AI-extracted lessons from incidents, cross-asset risk warnings, and recurring failure patterns.
        </p>
      </div>

      {/* Analysis Form */}
      <div className="industrial-card p-6 mb-8 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        <h2 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
          <Play size={18} style={{ color: '#6366f1' }} />
          Run Lessons Learned Analysis
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Analysis Scope */}
          <div>
            <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>Analysis Scope</label>
            <div className="relative">
              <select
                id="lessons-scope-select"
                value={analysisScope}
                onChange={e => setAnalysisScope(e.target.value as 'single' | 'cross_asset')}
                className="w-full px-4 py-3 rounded-xl text-sm outline-none appearance-none cursor-pointer"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                }}
              >
                <option value="cross_asset">Cross-Asset (all incidents)</option>
                <option value="single">Single Incident</option>
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--text-muted)' }} />
            </div>
          </div>

          {/* Equipment (optional) */}
          <div>
            <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>Equipment (optional)</label>
            <div className="relative">
              <select
                id="lessons-equipment-select"
                value={equipmentTag}
                onChange={e => setEquipmentTag(e.target.value)}
                className="w-full px-4 py-3 rounded-xl text-sm outline-none appearance-none cursor-pointer"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                }}
              >
                <option value="">All equipment</option>
                {industrialEquipment.map(eq => (
                  <option key={eq.tag} value={eq.tag}>{eq.tag} — {eq.name}</option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--text-muted)' }} />
            </div>
          </div>

          {/* Incident ID (optional) */}
          <div>
            <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>Incident ID (optional)</label>
            <input
              id="lessons-incident-id"
              type="text"
              value={incidentId}
              onChange={e => setIncidentId(e.target.value)}
              placeholder="e.g. INC-001"
              className="w-full px-4 py-3 rounded-xl text-sm outline-none"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
            />
          </div>
        </div>

        {/* Incident text (optional) */}
        <div className="mb-4">
          <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>
            Incident Description (optional — leave blank for cross-asset pattern analysis over all recorded incidents)
          </label>
          <textarea
            id="lessons-incident-text"
            value={incidentText}
            onChange={e => setIncidentText(e.target.value)}
            placeholder="Describe a specific incident to extract a targeted lesson from..."
            className="w-full px-4 py-3 rounded-xl text-sm outline-none resize-none"
            rows={3}
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
            }}
          />
        </div>

        <button
          id="run-lessons-btn"
          className="btn-primary w-full justify-center"
          onClick={runAnalysis}
          disabled={analyzing}
          style={{ padding: '12px' }}
        >
          {analyzing ? (
            <><Loader2 size={16} className="animate-spin" /> Analyzing...</>
          ) : (
            <><Lightbulb size={16} /> Run Analysis</>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-xl mb-6" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
          <div className="text-sm flex items-center gap-2" style={{ color: '#ef4444' }}>
            <AlertTriangle size={16} />
            {error}
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="animate-fade-in-up space-y-6">
          {/* Summary */}
          {(result.summary || result.recommendation) && (
            <div className="industrial-card p-6">
              <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>Summary</h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                {result.summary || result.recommendation}
              </p>
            </div>
          )}

          {/* Lessons */}
          {result.lessons && result.lessons.length > 0 && (
            <div className="industrial-card p-6">
              <h3 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                <Lightbulb size={18} style={{ color: '#eab308' }} />
                Lessons Extracted
                <span className="badge badge-operational">{result.lessons.length}</span>
              </h3>
              <div className="space-y-3">
                {result.lessons.map((lesson, i) => (
                  <div key={i} className="analysis-card">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      {lesson.severity && (
                        <span className={`badge badge-${RISK_BADGE[lesson.severity] || 'operational'}`}>{lesson.severity}</span>
                      )}
                      {lesson.category && (
                        <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>{lesson.category.replace(/_/g, ' ')}</span>
                      )}
                    </div>
                    <p className="text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>{lesson.lesson}</p>
                    {lesson.corrective_action && (
                      <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>
                        <span className="font-semibold" style={{ color: 'var(--text-muted)' }}>Corrective action: </span>
                        {lesson.corrective_action}
                      </div>
                    )}
                    {lesson.preventive_action && (
                      <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>
                        <span className="font-semibold" style={{ color: 'var(--text-muted)' }}>Preventive action: </span>
                        {lesson.preventive_action}
                      </div>
                    )}
                    <div className="flex gap-4 mt-2 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                      {lesson.equipment_tag && <span>Equipment: {lesson.equipment_tag}</span>}
                      {lesson.incident_id && <span>Incident: {lesson.incident_id}</span>}
                      {lesson.root_cause && <span>Root cause: {lesson.root_cause.replace(/_/g, ' ')}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cross-Asset Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="industrial-card p-6">
              <h3 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                <ShieldAlert size={18} style={{ color: '#ef4444' }} />
                Cross-Asset Warnings
                <span className="badge badge-critical">{result.warnings.length}</span>
              </h3>
              <div className="space-y-3">
                {result.warnings.map((w, i) => (
                  <div key={i} className="analysis-card">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`badge badge-${RISK_BADGE[w.risk_level] || 'operational'}`}>{w.risk_level}</span>
                        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{w.target_equipment}</span>
                      </div>
                      {w.based_on_incident && (
                        <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>from {w.based_on_incident}</span>
                      )}
                    </div>
                    <p className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>{w.risk_description}</p>
                    {w.recommended_action && (
                      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        <span className="font-semibold">Recommended: </span>{w.recommended_action}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Patterns */}
          {result.patterns && result.patterns.length > 0 && (
            <div className="industrial-card p-6">
              <h3 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                <TrendingUp size={18} style={{ color: '#3b82f6' }} />
                Recurring Patterns
                <span className="badge badge-operational">{result.patterns.length}</span>
              </h3>
              <div className="space-y-3">
                {result.patterns.map((p, i) => {
                  const TrendIcon = (p.trend && TREND_ICON[p.trend]) || Minus;
                  return (
                    <div key={i} className="analysis-card">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{p.pattern}</span>
                        <span className="flex items-center gap-1 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                          <TrendIcon size={11} /> {p.trend || 'unknown'}
                        </span>
                      </div>
                      {p.frequency && (
                        <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Frequency: {p.frequency}</div>
                      )}
                      {p.systemic_recommendation && (
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{p.systemic_recommendation}</p>
                      )}
                      {p.affected_assets && p.affected_assets.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {p.affected_assets.map((tag, j) => (
                            <span key={j} className="citation-card">{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <AgentReasoningPanel data={result} />
        </div>
      )}

      {/* Empty state */}
      {!result && !analyzing && !error && (
        <div className="text-center py-16 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <Lightbulb size={48} className="mx-auto mb-4 opacity-20" style={{ color: 'var(--text-muted)' }} />
          <p className="text-lg" style={{ color: 'var(--text-muted)' }}>
            Run a lessons learned analysis
          </p>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            The AI will extract actionable lessons, flag cross-asset risks, and detect recurring failure patterns.
          </p>
        </div>
      )}
    </div>
  );
}
