'use client';
import { useEffect } from 'react';
import { useSureflowStore } from '@/lib/store';
import { TrendingUp, Users, MessageSquare, BarChart2, FileText } from 'lucide-react';

function MetricCard({
  label, value, unit, icon: Icon, color, subtitle
}: {
  label: string;
  value: number | string;
  unit?: string;
  icon: React.ElementType;
  color: string;
  subtitle?: string;
}) {
  return (
    <div className="glass-card glass-card-hover p-6">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}22` }}>
          <Icon size={18} style={{ color }} />
        </div>
        <span className="font-medium text-sm" style={{ color: 'var(--text-secondary)' }}>{label}</span>
      </div>
      <div className="text-4xl font-extrabold mb-1" style={{ color: 'var(--text-primary)' }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
        {unit && <span className="text-lg font-medium ml-1" style={{ color: 'var(--text-muted)' }}>{unit}</span>}
      </div>
      {subtitle && <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{subtitle}</p>}
    </div>
  );
}

function ProgressBar({ value, color, label }: { value: number; color: string; label: string }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</span>
        <span className="text-xs font-bold" style={{ color }}>{value}%</span>
      </div>
      <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${value}%`, background: `linear-gradient(90deg, ${color}aa, ${color})` }}
        />
      </div>
    </div>
  );
}

export default function Analytics() {
  const { analytics, fetchAnalytics } = useSureflowStore();

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000);
    return () => clearInterval(interval);
  }, [fetchAnalytics]);

  const a = analytics;

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <span className="gradient-text">Analytics</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Business Analyst agent telemetry & performance insights</p>
      </div>

      {/* Primary KPIs */}
      <div className="grid grid-cols-3 gap-5 mb-8">
        <MetricCard
          label="Weekly Reach"
          value={a?.weekly_reach ?? 0}
          icon={TrendingUp}
          color="#6366f1"
          subtitle="Estimated impressions from posted content"
        />
        <MetricCard
          label="Qualified Rate"
          value={a?.qualified_rate ?? 0}
          unit="%"
          icon={Users}
          color="#10b981"
          subtitle="Leads with ICP score ≥ 7.0"
        />
        <MetricCard
          label="Reply Rate"
          value={a?.reply_rate ?? 0}
          unit="%"
          icon={MessageSquare}
          color="#06b6d4"
          subtitle="Leads with at least 1 touchpoint"
        />
      </div>

      {/* Secondary stats */}
      <div className="grid grid-cols-2 gap-5 mb-8">
        <MetricCard
          label="Total Posts"
          value={a?.total_posts ?? 0}
          icon={FileText}
          color="#f59e0b"
          subtitle="All-time published content"
        />
        <MetricCard
          label="Total Leads"
          value={a?.total_leads ?? 0}
          icon={BarChart2}
          color="#8b5cf6"
          subtitle="In CRM pipeline"
        />
      </div>

      {/* Funnel visualization */}
      <div className="glass-card p-6">
        <h2 className="font-semibold mb-6" style={{ color: 'var(--text-primary)' }}>Performance Funnel</h2>
        <div className="space-y-5">
          <ProgressBar value={100} color="#6366f1" label="Impressions (Reach)" />
          <ProgressBar value={a?.qualified_rate ?? 0} color="#10b981" label="Qualified Rate" />
          <ProgressBar value={a?.reply_rate ?? 0} color="#06b6d4" label="Reply / Touchpoint Rate" />
          <ProgressBar value={Math.min(a?.reply_rate ?? 0, 15)} color="#f59e0b" label="Meeting Booked Rate (est.)" />
        </div>
      </div>
    </div>
  );
}
