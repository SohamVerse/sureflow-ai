'use client';
import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useSureflowStore } from '@/lib/store';
import { useAuth } from '@/lib/AuthContext';
import { industrialApi } from '@/lib/api';
import type { MaintenanceResult } from '@/types';
import { AgentReasoningPanel } from '@/components/industrial/AgentReasoningPanel';
import {
  Wrench, AlertTriangle, Activity, Cpu, Loader2,
  ChevronDown, Play, ClipboardList,
} from 'lucide-react';

export default function MaintenanceDashboard() {
  const { industrialEquipment, fetchIndustrialEquipment } = useSureflowStore();
  const { targetPlantId } = useAuth();
  const [selectedTag, setSelectedTag] = useState('');
  const [analysisType, setAnalysisType] = useState('full');
  const [incidentContext, setIncidentContext] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<MaintenanceResult | null>(null);
  const [error, setError] = useState('');
  const [creatingWO, setCreatingWO] = useState<number | null>(null);

  useEffect(() => {
    fetchIndustrialEquipment();
  }, [fetchIndustrialEquipment, targetPlantId]);

  // Closed-loop: turn an AI recommendation into a tracked work order.
  const createWorkOrder = async (rec: { action: string; justification?: string; priority?: string; equipment_tag?: string }, i: number) => {
    setCreatingWO(i);
    try {
      const res = await industrialApi.createWorkOrder({
        title: rec.action,
        description: rec.justification || '',
        equipment_tag: rec.equipment_tag || selectedTag,
        type: (rec.priority === 'critical' || rec.priority === 'high') ? 'corrective' : 'preventive',
        status: 'open',
      });
      toast.success(`Work order ${res.wo_id} created`);
    } catch {
      toast.error('Failed to create work order');
    }
    setCreatingWO(null);
  };

  const runAnalysis = async () => {
    if (!selectedTag) return;
    setAnalyzing(true);
    setError('');
    setResult(null);
    try {
      const res = await industrialApi.analyzeMaintenance(selectedTag, analysisType, incidentContext);
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
          <Wrench size={28} className="inline mr-2" style={{ color: '#f59e0b' }} />
          Maintenance<span className="gradient-text"> Intelligence</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          AI-powered root cause analysis, failure prediction, and maintenance recommendations.
        </p>
      </div>

      {/* Analysis Form */}
      <div className="industrial-card p-6 mb-8 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        <h2 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
          <Play size={18} style={{ color: '#a855f7' }} />
          Run Analysis
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Equipment Selector */}
          <div>
            <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>Equipment Tag</label>
            <div className="relative">
              <select
                id="maintenance-equipment-select"
                value={selectedTag}
                onChange={e => setSelectedTag(e.target.value)}
                className="w-full px-4 py-3 rounded-xl text-sm outline-none appearance-none cursor-pointer"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                }}
              >
                <option value="">Select equipment...</option>
                {industrialEquipment.map(eq => (
                  <option key={eq.tag} value={eq.tag}>{eq.tag} — {eq.name}</option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--text-muted)' }} />
            </div>
          </div>

          {/* Analysis Type */}
          <div>
            <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>Analysis Type</label>
            <select
              id="analysis-type-select"
              value={analysisType}
              onChange={e => setAnalysisType(e.target.value)}
              className="w-full px-4 py-3 rounded-xl text-sm outline-none appearance-none cursor-pointer"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="full">Full Analysis (RCA + Prediction)</option>
              <option value="rca">Root Cause Analysis Only</option>
              <option value="prediction">Failure Prediction Only</option>
            </select>
          </div>

          {/* Run Button */}
          <div className="flex items-end">
            <button
              id="run-maintenance-btn"
              className="btn-primary w-full justify-center"
              onClick={runAnalysis}
              disabled={analyzing || !selectedTag}
              style={{ padding: '12px' }}
            >
              {analyzing ? (
                <><Loader2 size={16} className="animate-spin" /> Analyzing...</>
              ) : (
                <><Wrench size={16} /> Run Analysis</>
              )}
            </button>
          </div>
        </div>

        {/* Optional incident context */}
        <div>
          <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>
            Incident Context (optional)
          </label>
          <textarea
            id="incident-context"
            value={incidentContext}
            onChange={e => setIncidentContext(e.target.value)}
            placeholder="Describe any recent incident or symptoms for more targeted analysis..."
            className="w-full px-4 py-3 rounded-xl text-sm outline-none resize-none"
            rows={3}
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
            }}
          />
        </div>
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
        <div className="animate-fade-in-up">
          {/* Summary */}
          <div className="industrial-card p-6 mb-6">
            <h2 className="font-semibold text-lg mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <Activity size={18} style={{ color: '#22c55e' }} />
              Analysis Results — {result.equipment_tag}
            </h2>
            {(result.summary || result.recommendation) && (
              <div className="analysis-card mb-4">
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{result.summary || result.recommendation}</p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* RCA */}
              {result.rca && (
                <div className="analysis-card">
                  <div className="analysis-card-header">
                    <AlertTriangle size={16} style={{ color: '#ef4444' }} />
                    <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Root Cause Analysis</span>
                  </div>
                  <p className="text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}>
                    {result.rca.root_cause}
                  </p>
                  {result.rca.five_why_chain && result.rca.five_why_chain.length > 0 && (
                    <div className="space-y-2 mb-3">
                      <div className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>5-Why Chain:</div>
                      {result.rca.five_why_chain.map((why, i) => (
                        <div key={i} className="flex gap-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
                          <span className="font-bold min-w-6" style={{ color: '#f59e0b' }}>W{i + 1}</span>
                          <span>{why}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {result.rca.contributing_factors && result.rca.contributing_factors.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>Contributing Factors:</div>
                      {result.rca.contributing_factors.map((f, i) => (
                        <div key={i} className="text-xs flex gap-1 mb-1" style={{ color: 'var(--text-secondary)' }}>
                          <span style={{ color: '#ef4444' }}>•</span> {f}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Predictions */}
              {result.predictions && result.predictions.length > 0 && (
                <div className="analysis-card">
                  <div className="analysis-card-header">
                    <Activity size={16} style={{ color: '#a855f7' }} />
                    <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Failure Predictions</span>
                  </div>
                  <div className="space-y-4">
                    {result.predictions.map((pred, i) => (
                      <div key={i} className={i > 0 ? 'pt-4' : ''} style={i > 0 ? { borderTop: '1px solid var(--border)' } : undefined}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                            {pred.equipment_tag}{pred.equipment_name ? ` — ${pred.equipment_name}` : ''}
                          </span>
                          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{pred.timeframe}</span>
                        </div>
                        <div className="flex items-center gap-3 mb-2">
                          <div className="text-2xl font-bold" style={{
                            color: pred.probability > 70 ? '#ef4444' : pred.probability > 40 ? '#f59e0b' : '#22c55e'
                          }}>
                            {Math.round(pred.probability)}%
                          </div>
                          <div className="flex-1">
                            <div className="confidence-bar">
                              <div
                                className="confidence-bar-fill"
                                style={{
                                  width: `${pred.probability}%`,
                                  background: pred.probability > 70 ? '#ef4444' : pred.probability > 40 ? '#f59e0b' : '#22c55e',
                                }}
                              />
                            </div>
                          </div>
                        </div>
                        <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{pred.failure_mode}</div>
                        {pred.basis && (
                          <div className="text-[10px] mt-1" style={{ color: 'var(--text-muted)' }}>Basis: {pred.basis}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* MTBF / Similar Asset Analysis */}
            {result.similar_asset_analysis?.mtbf_estimate_hours && (
              <div className="mt-4 p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)' }}>
                <div className="flex items-center gap-3 mb-2">
                  <Cpu size={16} style={{ color: '#a855f7' }} />
                  <span className="text-sm" style={{ color: 'var(--text-muted)' }}>Estimated Mean Time Between Failures:</span>
                  <span className="text-lg font-bold" style={{ color: '#a855f7' }}>
                    {result.similar_asset_analysis.mtbf_estimate_hours.toLocaleString()} hours
                  </span>
                </div>
                {result.similar_asset_analysis.pattern_summary && (
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{result.similar_asset_analysis.pattern_summary}</p>
                )}
              </div>
            )}

            {/* Recommendations */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="analysis-card mt-4">
                <div className="analysis-card-header">
                  <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Recommendations</span>
                </div>
                <div className="space-y-3">
                  {result.recommendations.map((rec, i) => (
                    <div key={i} className="flex gap-3 text-sm items-start" style={{ color: 'var(--text-secondary)' }}>
                      <span style={{ color: '#22c55e' }}>✓</span>
                      <div className="flex-1">
                        <div>
                          {rec.action}
                          {rec.priority && (
                            <span className={`badge ml-2 badge-${rec.priority === 'critical' || rec.priority === 'high' ? 'critical' : 'operational'}`}>
                              {rec.priority}
                            </span>
                          )}
                        </div>
                        {rec.justification && (
                          <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{rec.justification}</div>
                        )}
                        {(rec.estimated_cost || rec.estimated_downtime) && (
                          <div className="text-[10px] mt-0.5 font-mono" style={{ color: 'var(--text-muted)' }}>
                            {rec.estimated_cost && <span>Cost: {rec.estimated_cost}</span>}
                            {rec.estimated_cost && rec.estimated_downtime && <span> · </span>}
                            {rec.estimated_downtime && <span>Downtime: {rec.estimated_downtime}</span>}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => createWorkOrder(rec, i)}
                        disabled={creatingWO === i}
                        className="btn-ghost flex-shrink-0"
                        style={{ padding: '5px 10px', fontSize: '11px' }}
                        title="Create a tracked work order from this recommendation"
                      >
                        {creatingWO === i ? <Loader2 size={12} className="animate-spin" /> : <ClipboardList size={12} />}
                        Work Order
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <AgentReasoningPanel data={result} />
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !analyzing && !error && (
        <div className="text-center py-16 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <Wrench size={48} className="mx-auto mb-4 opacity-20" style={{ color: 'var(--text-muted)' }} />
          <p className="text-lg" style={{ color: 'var(--text-muted)' }}>
            Select equipment and run an analysis
          </p>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            The AI will perform root cause analysis, failure prediction, and generate maintenance recommendations.
          </p>
        </div>
      )}
    </div>
  );
}
