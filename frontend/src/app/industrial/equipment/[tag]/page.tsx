'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { industrialApi } from '@/lib/api';
import { useSureflowStore } from '@/lib/store';
import { AssetTimeline } from '@/components/industrial/AssetTimeline';
import { SensorGauge } from '@/components/industrial/SensorGauge';
import Link from 'next/link';
import {
  ArrowLeft, Cpu, Activity, Wrench, AlertTriangle,
  Clock, MapPin, Loader2,
} from 'lucide-react';
import type { Equipment, AssetTimelineEvent, MaintenanceResult } from '@/types';

export default function EquipmentDetail() {
  const params = useParams();
  const tag = decodeURIComponent(params.tag as string);
  const { sensorData, fetchSensorData } = useSureflowStore();

  const [equipment, setEquipment] = useState<(Equipment & Record<string, unknown>) | null>(null);
  const [timeline, setTimeline] = useState<AssetTimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<MaintenanceResult | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [detail, timelineRes] = await Promise.all([
          industrialApi.getEquipmentDetail(tag),
          industrialApi.getTimeline(tag),
        ]);
        setEquipment(detail);
        setTimeline(timelineRes.timeline || []);
      } catch (e) {
        console.error('Failed to load equipment:', e);
      }
      setLoading(false);
    };
    load();
    fetchSensorData(tag);
  }, [tag, fetchSensorData]);

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      const result = await industrialApi.analyzeMaintenance(tag, 'full');
      setAnalysisResult(result);
    } catch (e) {
      console.error('Analysis failed:', e);
    }
    setAnalyzing(false);
  };

  if (loading) {
    return (
      <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
        <div className="space-y-4">
          <div className="skeleton h-8 w-64 rounded-lg" />
          <div className="skeleton h-48 rounded-2xl" />
          <div className="grid grid-cols-2 gap-4">
            <div className="skeleton h-64 rounded-2xl" />
            <div className="skeleton h-64 rounded-2xl" />
          </div>
        </div>
      </div>
    );
  }

  if (!equipment) {
    return (
      <div className="p-8 min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-primary)' }}>
        <div className="text-center">
          <Cpu size={48} className="mx-auto mb-4 opacity-30" style={{ color: 'var(--text-muted)' }} />
          <p style={{ color: 'var(--text-muted)' }}>Equipment &quot;{tag}&quot; not found.</p>
          <Link href="/industrial/equipment" className="text-sm mt-2 inline-block" style={{ color: '#a855f7' }}>
            ← Back to Equipment
          </Link>
        </div>
      </div>
    );
  }

  const statusColor =
    equipment.status === 'critical' ? '#ef4444' :
    equipment.status === 'warning' ? '#f59e0b' :
    equipment.status === 'offline' ? '#94a3b8' : '#22c55e';

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Back link */}
      <Link
        href="/industrial/equipment"
        className="flex items-center gap-1 text-sm mb-6 animate-fade-in-up"
        style={{ color: 'var(--text-muted)' }}
      >
        <ArrowLeft size={14} />
        Back to Equipment
      </Link>

      {/* Equipment Header */}
      <div className="industrial-card p-6 mb-8 animate-fade-in-up" style={{ animationDelay: '0.05s' }}>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center"
              style={{ background: `${statusColor}15` }}
            >
              <Cpu size={24} style={{ color: statusColor }} />
            </div>
            <div>
              <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                {equipment.tag}
              </h1>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{equipment.name}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`badge badge-${equipment.status}`} style={{ fontSize: '12px', padding: '4px 14px' }}>
              {equipment.status}
            </span>
            <button
              className="btn-primary text-sm"
              onClick={runAnalysis}
              disabled={analyzing}
            >
              {analyzing ? (
                <><Loader2 size={14} className="animate-spin" /> Analyzing...</>
              ) : (
                <><Wrench size={14} /> Run Maintenance Analysis</>
              )}
            </button>
          </div>
        </div>

        {/* Meta info */}
        <div className="flex flex-wrap gap-6 mt-5 pt-4" style={{ borderTop: '1px solid var(--border)' }}>
          {[
            { icon: MapPin, label: 'Area', value: equipment.area },
            { icon: Cpu, label: 'Type', value: equipment.type },
            { icon: Activity, label: 'Criticality', value: equipment.criticality },
            { icon: Clock, label: 'MTBF', value: equipment.mtbf_hours ? `${equipment.mtbf_hours.toLocaleString()}h` : 'N/A' },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="flex items-center gap-2">
              <Icon size={14} style={{ color: 'var(--text-muted)' }} />
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{label}:</span>
              <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Two Column: Sensors + Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Sensor Data */}
        <div className="industrial-card p-6 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
          <h2 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <Activity size={18} style={{ color: '#22c55e' }} />
            Live Sensor Data
            <span className="w-2 h-2 rounded-full sensor-live" style={{ background: '#22c55e' }} />
          </h2>
          {sensorData?.readings && sensorData.readings.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              {sensorData.readings.map((reading, i) => (
                <SensorGauge key={`${reading.sensor_type}-${i}`} reading={reading} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
              <Activity size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">No sensor data available.</p>
            </div>
          )}

          {/* Sensor Alerts */}
          {sensorData?.alerts && sensorData.alerts.length > 0 && (
            <div className="mt-6 pt-4" style={{ borderTop: '1px solid var(--border)' }}>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: '#ef4444' }}>
                <AlertTriangle size={14} />
                Active Alerts
              </h3>
              {sensorData.alerts.map((alert, i) => (
                <div
                  key={i}
                  className="p-3 rounded-lg mb-2"
                  style={{
                    background: alert.severity === 'critical' ? 'rgba(239,68,68,0.08)' : 'rgba(245,158,11,0.08)',
                    border: `1px solid ${alert.severity === 'critical' ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.2)'}`,
                  }}
                >
                  <div className="text-xs font-medium" style={{ color: alert.severity === 'critical' ? '#ef4444' : '#f59e0b' }}>
                    {alert.message}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Asset Timeline */}
        <div className="industrial-card p-6 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <h2 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <Clock size={18} style={{ color: '#a855f7' }} />
            Asset Timeline
          </h2>
          <div className="max-h-[500px] overflow-y-auto pr-2">
            <AssetTimeline events={timeline} />
          </div>
        </div>
      </div>

      {/* Maintenance Analysis Results */}
      {analysisResult && (
        <div className="industrial-card p-6 animate-fade-in-up" style={{ animationDelay: '0.25s' }}>
          <h2 className="font-semibold text-lg mb-5 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <Wrench size={18} style={{ color: '#f59e0b' }} />
            Maintenance Analysis Results
          </h2>

          {/* Summary */}
          {(analysisResult.summary || analysisResult.recommendation) && (
            <div className="analysis-card mb-4">
              <div className="analysis-card-header">
                <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Summary</span>
              </div>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{analysisResult.summary || analysisResult.recommendation}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* RCA */}
            {analysisResult.rca && (
              <div className="analysis-card">
                <div className="analysis-card-header">
                  <AlertTriangle size={16} style={{ color: '#ef4444' }} />
                  <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Root Cause Analysis</span>
                </div>
                <p className="text-sm font-medium mb-3" style={{ color: 'var(--text-primary)' }}>
                  {analysisResult.rca.root_cause}
                </p>
                {analysisResult.rca.five_why_chain && (
                  <div className="space-y-2">
                    <div className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>5-Why Chain:</div>
                    {analysisResult.rca.five_why_chain.map((why, i) => (
                      <div key={i} className="flex gap-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
                        <span className="font-bold" style={{ color: '#f59e0b' }}>W{i + 1}</span>
                        <span>{why}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Predictions */}
            {analysisResult.predictions && analysisResult.predictions.length > 0 && (
              <div className="analysis-card">
                <div className="analysis-card-header">
                  <Activity size={16} style={{ color: '#a855f7' }} />
                  <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Failure Prediction</span>
                </div>
                <div className="space-y-3">
                  {analysisResult.predictions.map((pred, i) => (
                    <div key={i} className={i > 0 ? 'pt-3' : ''} style={i > 0 ? { borderTop: '1px solid var(--border)' } : undefined}>
                      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{pred.equipment_tag} — Failure Probability</div>
                      <div className="text-2xl font-bold" style={{ color: pred.probability > 70 ? '#ef4444' : '#f59e0b' }}>
                        {Math.round(pred.probability)}%
                      </div>
                      <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Timeframe</div>
                      <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>{pred.timeframe}</div>
                      <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Failure Mode</div>
                      <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>{pred.failure_mode}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Recommendations */}
          {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
            <div className="analysis-card mt-4">
              <div className="analysis-card-header">
                <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Recommendations</span>
              </div>
              <ul className="space-y-2">
                {analysisResult.recommendations.map((rec, i) => (
                  <li key={i} className="flex gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                    <span style={{ color: '#22c55e' }}>•</span>
                    <span>
                      {rec.action}
                      {rec.priority && <span className="ml-2 text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>{rec.priority}</span>}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
