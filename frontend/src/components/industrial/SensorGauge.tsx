'use client';
import type { SensorReading } from '@/types';

interface SensorGaugeProps {
  reading: SensorReading;
  size?: number;
}

export function SensorGauge({ reading, size = 100 }: SensorGaugeProps) {
  const { sensor_type, value, unit, status, threshold_high, threshold_low } = reading;

  // Calculate fill percentage
  const max = threshold_high || 100;
  const min = threshold_low || 0;
  const range = max - min;
  const pct = Math.min(1, Math.max(0, (value - min) / range));

  // Arc parameters (270 degree arc)
  const radius = (size - 16) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * radius * (270 / 360);
  const offset = circumference * (1 - pct);

  const statusClass = `sensor-gauge-${status}`;

  const formatLabel = (type: string) =>
    type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="sensor-gauge" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background arc */}
          <circle
            className="sensor-gauge-ring sensor-gauge-bg"
            cx={cx}
            cy={cy}
            r={radius}
            strokeDasharray={`${circumference} ${2 * Math.PI * radius}`}
            strokeDashoffset={0}
            style={{ transform: 'rotate(-225deg)', transformOrigin: 'center' }}
          />
          {/* Value arc */}
          <circle
            className={`sensor-gauge-ring ${statusClass}`}
            cx={cx}
            cy={cy}
            r={radius}
            strokeDasharray={`${circumference} ${2 * Math.PI * radius}`}
            strokeDashoffset={offset}
            style={{ transform: 'rotate(-225deg)', transformOrigin: 'center' }}
          />
        </svg>
        {/* Center value */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center"
          style={{ top: '-2px' }}
        >
          <span className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
            {value.toFixed(1)}
          </span>
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{unit}</span>
        </div>
      </div>
      <div className="text-center">
        <div className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
          {formatLabel(sensor_type)}
        </div>
        <div className={`text-[10px] font-semibold badge badge-${status === 'normal' ? 'operational' : status}`} style={{ marginTop: '4px' }}>
          {status.toUpperCase()}
        </div>
      </div>
    </div>
  );
}
