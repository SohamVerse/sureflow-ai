'use client';
import Link from 'next/link';
import type { Equipment } from '@/types';
import { Cpu, Activity } from 'lucide-react';

interface EquipmentCardProps {
  equipment: Equipment;
  delay?: number;
}

const STATUS_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  operational: { bg: 'rgba(34,197,94,0.1)', color: '#22c55e', label: 'Operational' },
  warning:     { bg: 'rgba(245,158,11,0.1)', color: '#f59e0b', label: 'Warning' },
  critical:    { bg: 'rgba(239,68,68,0.1)', color: '#ef4444', label: 'Critical' },
  offline:     { bg: 'rgba(100,116,139,0.1)', color: '#94a3b8', label: 'Offline' },
};

export function EquipmentCard({ equipment, delay = 0 }: EquipmentCardProps) {
  const status = STATUS_STYLES[equipment.status] || STATUS_STYLES.operational;

  return (
    <Link href={`/industrial/equipment/${encodeURIComponent(equipment.tag)}`}>
      <div
        className="industrial-card p-5 cursor-pointer animate-fade-in-up"
        style={{ animationDelay: `${delay}s` }}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: status.bg }}
            >
              <Cpu size={16} style={{ color: status.color }} />
            </div>
            <div>
              <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                {equipment.tag}
              </div>
              <div className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                {equipment.type}
              </div>
            </div>
          </div>
          <span className={`badge badge-${equipment.status}`}>
            {status.label}
          </span>
        </div>

        <div className="text-xs mb-3" style={{ color: 'var(--text-secondary)' }}>
          {equipment.name}
        </div>

        <div className="flex items-center justify-between text-[11px]" style={{ color: 'var(--text-muted)' }}>
          <span>Area: {equipment.area}</span>
          <span className="flex items-center gap-1">
            <Activity size={10} />
            {equipment.criticality}
          </span>
        </div>

        {equipment.mtbf_hours && (
          <div className="mt-2 text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>
            MTBF: {equipment.mtbf_hours.toLocaleString()}h
          </div>
        )}
      </div>
    </Link>
  );
}
