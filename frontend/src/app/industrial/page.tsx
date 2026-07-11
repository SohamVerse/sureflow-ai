'use client';
import { useEffect } from 'react';
import { useSureflowStore } from '@/lib/store';
import { KPICard } from '@/components/industrial/KPICard';
import { PlantHierarchyTree } from '@/components/industrial/PlantHierarchyTree';
import {
  Factory, Cpu, AlertTriangle, Wrench, BookOpen,
  Shield, Activity, TrendingUp,
} from 'lucide-react';
import Link from 'next/link';

export default function IndustrialDashboard() {
  const {
    industrialOverview, industrialKPIs, industrialHierarchy, industrialIncidents,
    fetchIndustrialOverview, fetchIndustrialKPIs, fetchIndustrialHierarchy, fetchIndustrialIncidents,
  } = useSureflowStore();

  useEffect(() => {
    fetchIndustrialOverview();
    fetchIndustrialKPIs();
    fetchIndustrialHierarchy();
    fetchIndustrialIncidents();
  }, [fetchIndustrialOverview, fetchIndustrialKPIs, fetchIndustrialHierarchy, fetchIndustrialIncidents]);

  const overview = industrialOverview;
  const kpis = industrialKPIs;

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          Industrial<span className="gradient-text"> Intelligence</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Plant overview, real-time equipment monitoring, and AI-powered maintenance intelligence.
        </p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KPICard
          label="Total Equipment"
          value={overview?.equipment ?? 0}
          icon={Cpu}
          color="#3b82f6"
          delay={0.1}
        />
        <KPICard
          label="Open Incidents"
          value={overview?.incidents ?? 0}
          icon={AlertTriangle}
          color="#ef4444"
          delay={0.15}
        />
        <KPICard
          label="Work Orders"
          value={overview?.work_orders ?? 0}
          icon={Wrench}
          color="#f59e0b"
          delay={0.2}
        />
        <KPICard
          label="Lessons Learned"
          value={kpis?.lessons_learned_count ?? 0}
          icon={BookOpen}
          color="#22c55e"
          delay={0.25}
        />
      </div>

      {/* Two column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Plant Hierarchy */}
        <div className="industrial-card p-6 animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-semibold text-lg flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <Factory size={18} style={{ color: '#6366f1' }} />
              Plant Hierarchy
            </h2>
          </div>
          <PlantHierarchyTree nodes={industrialHierarchy} />
        </div>

        {/* Graph Overview */}
        <div className="industrial-card p-6 animate-fade-in-up" style={{ animationDelay: '0.35s' }}>
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-semibold text-lg flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <Activity size={18} style={{ color: '#06b6d4' }} />
              Knowledge Graph Stats
            </h2>
          </div>
          {overview ? (
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'Plants', value: overview.plants, color: '#6366f1' },
                { label: 'Areas', value: overview.areas, color: '#06b6d4' },
                { label: 'Equipment', value: overview.equipment, color: '#3b82f6' },
                { label: 'Incidents', value: overview.incidents, color: '#ef4444' },
                { label: 'Work Orders', value: overview.work_orders, color: '#f59e0b' },
                { label: 'Inspections', value: overview.inspections, color: '#22c55e' },
                { label: 'Documents', value: overview.documents, color: '#a855f7' },
                { label: 'Safety Incidents', value: kpis?.safety_incidents ?? 0, color: '#dc2626' },
              ].map((item) => (
                <div
                  key={item.label}
                  className="p-4 rounded-xl"
                  style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)' }}
                >
                  <div className="text-2xl font-bold mb-1" style={{ color: item.color }}>
                    {item.value}
                  </div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{item.label}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="skeleton h-10 rounded-lg" />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Incidents */}
      <div className="industrial-card p-6 animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-lg flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <AlertTriangle size={18} style={{ color: '#ef4444' }} />
            Recent Incidents
          </h2>
          <div className="flex gap-2">
            <Link
              href="/industrial/maintenance"
              className="text-xs px-3 py-1.5 rounded-lg"
              style={{ background: 'rgba(245,158,11,0.1)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.2)' }}
            >
              <Wrench size={12} className="inline mr-1" />
              Maintenance
            </Link>
            <Link
              href="/industrial/compliance"
              className="text-xs px-3 py-1.5 rounded-lg"
              style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.2)' }}
            >
              <Shield size={12} className="inline mr-1" />
              Compliance
            </Link>
          </div>
        </div>

        {industrialIncidents.length === 0 ? (
          <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
            <Shield size={40} className="mx-auto mb-3 opacity-30" />
            <p>No incidents recorded. All clear.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {industrialIncidents.slice(0, 8).map((incident, i) => (
              <div
                key={incident.id}
                className="flex items-center gap-4 p-4 rounded-xl animate-fade-in-up"
                style={{
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border)',
                  animationDelay: `${0.45 + i * 0.03}s`,
                }}
              >
                <div
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{
                    background:
                      incident.severity === 'critical' ? '#ef4444' :
                      incident.severity === 'high' ? '#f59e0b' :
                      incident.severity === 'medium' ? '#06b6d4' : '#22c55e',
                    boxShadow:
                      incident.severity === 'critical' ? '0 0 8px rgba(239,68,68,0.5)' : 'none',
                  }}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                    {incident.title}
                  </div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {incident.equipment_tag} · {new Date(incident.date).toLocaleDateString()}
                  </div>
                </div>
                <span className={`badge badge-${incident.severity === 'critical' ? 'critical' : incident.severity === 'high' ? 'warning' : 'operational'}`}>
                  {incident.severity}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
        {[
          { href: '/industrial/copilot', label: 'Ask Copilot', icon: TrendingUp, desc: 'Chat with AI', color: '#6366f1' },
          { href: '/industrial/equipment', label: 'Equipment', icon: Cpu, desc: 'Browse assets', color: '#3b82f6' },
          { href: '/industrial/upload', label: 'Upload Doc', icon: BookOpen, desc: 'Ingest documents', color: '#a855f7' },
          { href: '/industrial/maintenance', label: 'Run Analysis', icon: Wrench, desc: 'Maintenance AI', color: '#f59e0b' },
        ].map((action, i) => (
          <Link key={action.href} href={action.href}>
            <div
              className="industrial-card p-5 cursor-pointer animate-fade-in-up"
              style={{ animationDelay: `${0.5 + i * 0.05}s` }}
            >
              <action.icon size={20} style={{ color: action.color, marginBottom: '12px' }} />
              <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{action.label}</div>
              <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{action.desc}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
