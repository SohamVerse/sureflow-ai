'use client';
import type { LucideIcon } from 'lucide-react';

interface KPICardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  color: string;
  delay?: number;
  subtitle?: string;
}

export function KPICard({ label, value, icon: Icon, color, delay = 0, subtitle }: KPICardProps) {
  const rgbMap: Record<string, string> = {
    '#6366f1': '99,102,241',
    '#06b6d4': '6,182,212',
    '#3b82f6': '59,130,246',
    '#10b981': '16,185,129',
    '#22c55e': '34,197,94',
    '#f59e0b': '245,158,11',
    '#ef4444': '239,68,68',
    '#f97316': '249,115,22',
    '#a855f7': '168,85,247',
  };
  const rgb = rgbMap[color] || '99,102,241';

  return (
    <div
      className="industrial-card p-6 animate-fade-in-up"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="flex items-center justify-between mb-4">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: `rgba(${rgb},0.12)` }}
        >
          <Icon size={18} style={{ color }} />
        </div>
      </div>
      <div className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      <div className="text-sm" style={{ color: 'var(--text-muted)' }}>{label}</div>
      {subtitle && (
        <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>{subtitle}</div>
      )}
    </div>
  );
}
