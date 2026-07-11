'use client';
import type { AssetTimelineEvent } from '@/types';
import { AlertTriangle, Wrench, ClipboardCheck } from 'lucide-react';

interface AssetTimelineProps {
  events: AssetTimelineEvent[];
}

const TYPE_CONFIG: Record<string, { icon: typeof AlertTriangle; color: string; label: string }> = {
  incident: { icon: AlertTriangle, color: '#ef4444', label: 'Incident' },
  work_order: { icon: Wrench, color: '#f59e0b', label: 'Work Order' },
  inspection: { icon: ClipboardCheck, color: '#22c55e', label: 'Inspection' },
};

export function AssetTimeline({ events }: AssetTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="text-center py-12" style={{ color: 'var(--text-muted)' }}>
        <ClipboardCheck size={40} className="mx-auto mb-3 opacity-30" />
        <p>No timeline events found.</p>
      </div>
    );
  }

  return (
    <div className="timeline-container">
      {events.map((event, i) => {
        const config = TYPE_CONFIG[event.type] || TYPE_CONFIG.incident;
        const Icon = config.icon;
        return (
          <div
            key={`${event.type}-${event.id}-${i}`}
            className={`timeline-node type-${event.type}`}
            style={{ animationDelay: `${i * 0.05}s` }}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <Icon size={14} style={{ color: config.color }} />
                <span className="badge" style={{
                  background: `${config.color}15`,
                  color: config.color,
                  border: `1px solid ${config.color}30`,
                }}>
                  {config.label}
                </span>
                {event.severity && (
                  <span className={`text-[10px] font-semibold severity-${event.severity}`}>
                    {event.severity.toUpperCase()}
                  </span>
                )}
              </div>
              <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>
                {new Date(event.date).toLocaleDateString()}
              </span>
            </div>
            <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
              {event.title}
            </div>
            {event.description && (
              <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                {event.description}
              </div>
            )}
            {event.status && (
              <div className="text-[10px] mt-2 font-mono" style={{ color: 'var(--text-muted)' }}>
                Status: {event.status}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
