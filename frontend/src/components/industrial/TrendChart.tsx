'use client';
import { useRef, useState } from 'react';

interface TrendChartProps {
  title: string;
  data: number[];
  labels: string[];
  color: string;
  goodDirection?: 'up' | 'down'; // colors the delta chip
}

// Single-series line chart: 2px line, recessive baseline, direct last-value
// label, hover crosshair+tooltip. One series → no legend (the title names it).
export function TrendChart({ title, data, labels, color, goodDirection = 'up' }: TrendChartProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<number | null>(null);

  const W = 320, H = 120, padX = 8, padY = 14;
  const n = data.length;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const span = max - min || 1;
  const x = (i: number) => padX + (i * (W - 2 * padX)) / Math.max(1, n - 1);
  const y = (v: number) => padY + (1 - (v - min) / span) * (H - 2 * padY);

  const line = data.map((v, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  const area = `${line} L${x(n - 1).toFixed(1)},${H - padY} L${x(0).toFixed(1)},${H - padY} Z`;

  const first = data[0] ?? 0, last = data[n - 1] ?? 0;
  const delta = last - first;
  const deltaGood = goodDirection === 'up' ? delta >= 0 : delta <= 0;

  const onMove = (e: React.MouseEvent) => {
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect) return;
    const rel = (e.clientX - rect.left) / rect.width;
    setHover(Math.max(0, Math.min(n - 1, Math.round(rel * (n - 1)))));
  };

  return (
    <div className="industrial-card p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{title}</span>
        <span className="text-xs font-bold px-2 py-0.5 rounded" style={{
          background: deltaGood ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
          color: deltaGood ? '#22c55e' : '#ef4444',
        }}>
          {delta >= 0 ? '+' : ''}{delta} over {n} pts
        </span>
      </div>
      <div ref={wrapRef} className="relative" onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ display: 'block', overflow: 'visible' }}>
          {/* recessive baseline */}
          <line x1={padX} y1={H - padY} x2={W - padX} y2={H - padY} stroke="var(--border)" strokeWidth={1} />
          <defs>
            <linearGradient id={`g-${title.replace(/\s/g, '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.22} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <path d={area} fill={`url(#g-${title.replace(/\s/g, '')})`} />
          <path d={line} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
          {/* last-value direct label */}
          <circle cx={x(n - 1)} cy={y(last)} r={3} fill={color} />
          <text x={x(n - 1) - 4} y={y(last) - 6} textAnchor="end" fontSize={11} fontWeight={700} fill="var(--text-primary)">{last}</text>
          {/* hover crosshair */}
          {hover != null && (
            <>
              <line x1={x(hover)} y1={padY} x2={x(hover)} y2={H - padY} stroke={color} strokeWidth={1} strokeDasharray="3 3" opacity={0.6} />
              <circle cx={x(hover)} cy={y(data[hover])} r={4} fill={color} stroke="var(--bg-primary)" strokeWidth={2} />
            </>
          )}
        </svg>
        {hover != null && (
          <div className="absolute pointer-events-none px-2 py-1 rounded-lg text-[11px]" style={{
            left: `${(hover / Math.max(1, n - 1)) * 100}%`, top: -4, transform: 'translate(-50%, -100%)',
            background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)', whiteSpace: 'nowrap',
          }}>
            <span className="font-bold">{data[hover]}</span> <span style={{ color: 'var(--text-muted)' }}>{labels[hover]}</span>
          </div>
        )}
      </div>
    </div>
  );
}
