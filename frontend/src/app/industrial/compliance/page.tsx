'use client';
import { useEffect, useState } from 'react';
import { useSureflowStore } from '@/lib/store';
import { useAuth } from '@/lib/AuthContext';
import { industrialApi } from '@/lib/api';
import type { ComplianceResult } from '@/types';
import { AgentReasoningPanel } from '@/components/industrial/AgentReasoningPanel';
import {
  ClipboardCheck, Shield, AlertTriangle, Loader2,
  ChevronDown, Play, CheckCircle, XCircle,
} from 'lucide-react';

export default function ComplianceDashboard() {
  const { industrialEquipment, fetchIndustrialEquipment } = useSureflowStore();
  const { targetPlantId } = useAuth();
  const [scope, setScope] = useState('facility');
  const [areaId, setAreaId] = useState('');
  const [equipmentTag, setEquipmentTag] = useState('');
  const [regulationFocus, setRegulationFocus] = useState('');
  const [auditing, setAuditing] = useState(false);
  const [result, setResult] = useState<ComplianceResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchIndustrialEquipment();
  }, [fetchIndustrialEquipment, targetPlantId]);

  const areas = [...new Set(industrialEquipment.map(e => e.area_id))].sort();

  const runAudit = async () => {
    setAuditing(true);
    setError('');
    setResult(null);
    try {
      const res = await industrialApi.analyzeCompliance(scope, areaId, equipmentTag, regulationFocus);
      setResult(res);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Audit failed';
      setError(msg);
    }
    setAuditing(false);
  };

  // Audit readiness gauge — driven by compliance_score (0-100), the only
  // numeric readiness field the Compliance Agent actually returns.
  const readinessScore = result?.compliance_score ?? 0;
  const circumference = 2 * Math.PI * 45;
  const offset = circumference * (1 - readinessScore / 100);
  const scoreColor = readinessScore >= 80 ? '#22c55e' : readinessScore >= 50 ? '#f59e0b' : '#ef4444';

  // SOP compliance counts derived client-side from sop_gaps — the agent
  // returns a per-SOP status list, not a pre-aggregated total/compliant count.
  const sopGaps = result?.sop_gaps ?? [];
  const sopCompliant = sopGaps.filter(g => g.status === 'adequate').length;
  const sopTotal = sopGaps.length;

  const gapSeverityBadge = (severity: string) =>
    severity === 'critical' ? 'critical' : severity === 'major' ? 'warning' : 'operational';

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <ClipboardCheck size={28} className="inline mr-2" style={{ color: '#22c55e' }} />
          Compliance<span className="gradient-text"> Dashboard</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          AI-powered regulatory gap analysis, SOP compliance checks, and audit readiness assessment.
        </p>
      </div>

      {/* Audit Form */}
      <div className="industrial-card p-6 mb-8 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        <h2 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
          <Play size={18} style={{ color: '#a855f7' }} />
          Run Compliance Audit
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          {/* Scope */}
          <div>
            <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>Scope</label>
            <select
              id="compliance-scope"
              value={scope}
              onChange={e => setScope(e.target.value)}
              className="w-full px-4 py-3 rounded-xl text-sm outline-none appearance-none cursor-pointer"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
            >
              <option value="facility">Facility-wide</option>
              <option value="area">By Area</option>
              <option value="equipment">By Equipment</option>
            </select>
          </div>

          {/* Area (conditional) */}
          {scope === 'area' && (
            <div>
              <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>Area</label>
              <select
                value={areaId}
                onChange={e => setAreaId(e.target.value)}
                className="w-full px-4 py-3 rounded-xl text-sm outline-none appearance-none cursor-pointer"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                }}
              >
                <option value="">Select area...</option>
                {areas.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
          )}

          {/* Equipment (conditional) */}
          {scope === 'equipment' && (
            <div>
              <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>Equipment</label>
              <select
                value={equipmentTag}
                onChange={e => setEquipmentTag(e.target.value)}
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
            </div>
          )}

          {/* Regulation Focus */}
          <div>
            <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>Regulation Focus</label>
            <input
              type="text"
              value={regulationFocus}
              onChange={e => setRegulationFocus(e.target.value)}
              placeholder="e.g. OSHA, ISO 14001..."
              className="w-full px-4 py-3 rounded-xl text-sm outline-none"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          {/* Run Button */}
          <div className="flex items-end">
            <button
              id="run-audit-btn"
              className="btn-primary w-full justify-center"
              onClick={runAudit}
              disabled={auditing}
              style={{ padding: '12px' }}
            >
              {auditing ? (
                <><Loader2 size={16} className="animate-spin" /> Auditing...</>
              ) : (
                <><Shield size={16} /> Run Audit</>
              )}
            </button>
          </div>
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
          {/* Top row: Score + SOP */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {/* Audit Readiness Score */}
            <div className="industrial-card p-6 flex flex-col items-center justify-center">
              <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-muted)' }}>Audit Readiness</h3>
              <svg width={120} height={120} className="progress-ring">
                <circle className="progress-ring-bg" cx="60" cy="60" r="45" />
                <circle
                  className="progress-ring-fill"
                  cx="60" cy="60" r="45"
                  stroke={scoreColor}
                  strokeDasharray={circumference}
                  strokeDashoffset={offset}
                />
              </svg>
              <div className="text-3xl font-bold mt-4" style={{ color: scoreColor }}>
                {readinessScore}%
              </div>
              <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                {result.audit_readiness?.overall_status
                  ? result.audit_readiness.overall_status.replace('_', ' ')
                  : (readinessScore >= 80 ? 'Audit Ready' : readinessScore >= 50 ? 'Needs Improvement' : 'At Risk')}
              </div>
            </div>

            {/* SOP Compliance */}
            <div className="industrial-card p-6">
              <h3 className="text-sm font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-muted)' }}>
                <ClipboardCheck size={14} />
                SOP Compliance
              </h3>
              {sopTotal > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Total SOPs Reviewed</span>
                    <span className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{sopTotal}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs flex items-center gap-1" style={{ color: '#22c55e' }}>
                      <CheckCircle size={12} /> Adequate
                    </span>
                    <span className="text-lg font-bold" style={{ color: '#22c55e' }}>{sopCompliant}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs flex items-center gap-1" style={{ color: '#ef4444' }}>
                      <XCircle size={12} /> Needs Update / Missing
                    </span>
                    <span className="text-lg font-bold" style={{ color: '#ef4444' }}>{sopTotal - sopCompliant}</span>
                  </div>
                  {/* Compliance bar */}
                  <div className="confidence-bar" style={{ height: '8px' }}>
                    <div
                      className="confidence-bar-fill"
                      style={{
                        width: `${sopTotal > 0 ? (sopCompliant / sopTotal * 100) : 0}%`,
                        background: 'linear-gradient(90deg, #22c55e, #10b981)',
                      }}
                    />
                  </div>
                </div>
              ) : (
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No SOP gaps identified for this scope.</p>
              )}
            </div>

            {/* Summary */}
            <div className="industrial-card p-6">
              <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--text-muted)' }}>Summary</h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                {result.summary || result.recommendation}
              </p>
            </div>
          </div>

          {/* Gaps */}
          {result.gaps && result.gaps.length > 0 && (
            <div className="industrial-card p-6 mb-6">
              <h3 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                <AlertTriangle size={18} style={{ color: '#ef4444' }} />
                Compliance Gaps
                <span className="badge badge-critical">{result.gaps.length}</span>
              </h3>
              <div className="space-y-3">
                {result.gaps.map((gap, i) => (
                  <div
                    key={i}
                    className="analysis-card"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`badge badge-${gapSeverityBadge(gap.severity)}`}>
                          {gap.severity}
                        </span>
                        {gap.requirement && (
                          <span className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                            {gap.requirement}
                          </span>
                        )}
                      </div>
                      {gap.regulation && (
                        <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>
                          {gap.regulation}
                        </span>
                      )}
                    </div>
                    <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{gap.finding}</p>
                    {gap.remediation && (
                      <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Remediation: {gap.remediation}</p>
                    )}
                    <div className="flex gap-4 mt-2 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                      {gap.area && <span>Area: {gap.area}</span>}
                      {gap.equipment_tag && <span>Equipment: {gap.equipment_tag}</span>}
                      {gap.due_date && <span>Due: {gap.due_date}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div className="industrial-card p-6">
              <h3 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                <CheckCircle size={18} style={{ color: '#22c55e' }} />
                Recommendations
              </h3>
              <div className="space-y-2">
                {result.recommendations.map((rec, i) => (
                  <div key={i} className="flex gap-3 p-3 rounded-lg text-sm" style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid var(--border)',
                    color: 'var(--text-secondary)',
                  }}>
                    <span style={{ color: '#22c55e' }}>✓</span>
                    <div>
                      <div>
                        {rec.action}
                        {rec.priority && <span className="ml-2 text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>{rec.priority.replace(/_/g, ' ')}</span>}
                      </div>
                      {(rec.regulation || rec.responsible_party || rec.deadline) && (
                        <div className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
                          {rec.regulation && <span>{rec.regulation}</span>}
                          {rec.responsible_party && <span> · {rec.responsible_party}</span>}
                          {rec.deadline && <span> · Due {rec.deadline}</span>}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <AgentReasoningPanel data={result} />
        </div>
      )}

      {/* Empty state */}
      {!result && !auditing && !error && (
        <div className="text-center py-16 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <Shield size={48} className="mx-auto mb-4 opacity-20" style={{ color: 'var(--text-muted)' }} />
          <p className="text-lg" style={{ color: 'var(--text-muted)' }}>
            Configure scope and run an audit
          </p>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            The AI will identify regulatory gaps, check SOP compliance, and assess audit readiness.
          </p>
        </div>
      )}
    </div>
  );
}
