'use client';
import { useEffect, useRef, useState } from 'react';
import { FunnelModel } from './FunnelModel';

interface FeatureBlock {
  title: string;
  description: string;
}

const FEATURES: FeatureBlock[] = [
  {
    title: 'Process every alert',
    description:
      'Automatically ingest, deduplicate, and correlate every alert from across your operational stack — no signal is ever missed or buried.',
  },
  {
    title: 'Develop High-Fidelity Incidents',
    description:
      'Enrich raw alerts with contextual telemetry, asset metadata, and historical patterns to build actionable, high-fidelity incident reports.',
  },
  {
    title: 'Activate Your Data',
    description:
      'Transform siloed sensor readings and logs into unified, real-time intelligence that drives faster, smarter operational decisions.',
  },
  {
    title: 'Accelerate Response',
    description:
      'Execute automated playbooks and remediation workflows in seconds, dramatically reducing mean time to resolution across your operations.',
  },
];

export function ProcessSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
        }
      },
      { threshold: 0.15 }
    );
    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }
    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={sectionRef}
      style={{
        position: 'relative',
        background: 'var(--bg-primary)',
        padding: '120px 0 140px',
        overflow: 'hidden',
      }}
    >
      <style
        dangerouslySetInnerHTML={{
          __html: `
          /* ── Grid Background ───────────────────────────── */
          .process-grid-bg {
            position: absolute;
            inset: 0;
            background-image:
              linear-gradient(rgba(139, 92, 246, 0.03) 1px, transparent 1px),
              linear-gradient(90deg, rgba(139, 92, 246, 0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            pointer-events: none;
          }

          /* ── Radial glow behind the funnel ──────────────── */
          .process-radial-glow {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 700px;
            height: 700px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, rgba(139, 92, 246, 0.04) 40%, transparent 70%);
            pointer-events: none;
            z-index: 0;
          }

          /* ── Entrance Animations ────────────────────────── */
          @keyframes processFadeUp {
            from { opacity: 0; transform: translateY(40px); }
            to   { opacity: 1; transform: translateY(0); }
          }
          @keyframes processFadeLeft {
            from { opacity: 0; transform: translateX(-50px); }
            to   { opacity: 1; transform: translateX(0); }
          }
          @keyframes processFadeRight {
            from { opacity: 0; transform: translateX(50px); }
            to   { opacity: 1; transform: translateX(0); }
          }
          @keyframes processScaleIn {
            from { opacity: 0; transform: scale(0.85); }
            to   { opacity: 1; transform: scale(1); }
          }
          @keyframes floatSlow {
            0%, 100% { transform: translateY(0); }
            50%      { transform: translateY(-12px); }
          }

          .process-animate-left {
            opacity: 0;
          }
          .process-animate-left.active {
            animation: processFadeLeft 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          }
          .process-animate-right {
            opacity: 0;
          }
          .process-animate-right.active {
            animation: processFadeRight 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          }
          .process-animate-center {
            opacity: 0;
          }
          .process-animate-center.active {
            animation: processScaleIn 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          }
          .process-float {
            animation: floatSlow 6s ease-in-out infinite;
          }

          /* ── Connection Lines (dashed) ──────────────────── */
          .process-connection-line {
            position: absolute;
            z-index: 1;
          }

          /* ── Floating Icon Badges ──────────────────────── */
          .process-icon-badge {
            position: absolute;
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            z-index: 3;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
          }

          /* ── Main Layout ───────────────────────────────── */
          .process-layout {
            position: relative;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 24px;
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            grid-template-rows: auto auto;
            align-items: center;
            min-height: 650px;
            z-index: 2;
          }

          /* Center image column spans both rows */
          .process-center-col {
            grid-column: 2;
            grid-row: 1 / 3;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
          }

          .process-text-block {
            padding: 0 20px;
          }
          .process-text-block h3 {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0 0 12px 0;
            letter-spacing: -0.01em;
            line-height: 1.3;
          }
          .process-text-block p {
            font-size: 14px;
            line-height: 1.7;
            color: var(--text-secondary);
            margin: 0;
          }

          /* ── Corner Decoration Dots ─────────────────────── */
          .process-corner-dot {
            position: absolute;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: rgba(139, 92, 246, 0.4);
            z-index: 1;
          }

          /* ── Responsive ─────────────────────────────────── */
          @media (max-width: 900px) {
            .process-layout {
              grid-template-columns: 1fr;
              grid-template-rows: auto;
              gap: 40px;
              min-height: auto;
            }
            .process-center-col {
              grid-column: 1;
              grid-row: auto;
              order: -1;
            }
            .process-text-block {
              text-align: center;
              padding: 0;
            }
            .process-icon-badge {
              display: none;
            }
            .process-connection-line {
              display: none;
            }
          }
        `,
        }}
      />

      {/* Background grid */}
      <div className="process-grid-bg" />

      {/* Radial glow */}
      <div className="process-radial-glow" />

      {/* Scattered corner decoration dots */}
      <div className="process-corner-dot" style={{ top: '15%', left: '8%' }} />
      <div className="process-corner-dot" style={{ top: '25%', right: '12%' }} />
      <div className="process-corner-dot" style={{ bottom: '20%', left: '15%' }} />
      <div className="process-corner-dot" style={{ bottom: '10%', right: '10%' }} />
      <div className="process-corner-dot" style={{ top: '60%', left: '5%' }} />
      <div className="process-corner-dot" style={{ top: '40%', right: '6%' }} />

      {/* ── Main 3-Column Layout ─────────────────────────── */}
      <div className="process-layout">
        {/* ── LEFT COLUMN: Feature 1 (top) & Feature 2 (bottom) ── */}
        <div
          style={{
            gridColumn: 1,
            gridRow: 1,
            alignSelf: 'center',
            paddingBottom: '30px',
          }}
        >
          <div
            className={`process-text-block process-animate-left ${isInView ? 'active' : ''}`}
            style={{ animationDelay: '0.1s' }}
          >
            <h3>{FEATURES[0].title}</h3>
            <p>{FEATURES[0].description}</p>
          </div>
        </div>

        <div
          style={{
            gridColumn: 1,
            gridRow: 2,
            alignSelf: 'center',
            paddingTop: '30px',
          }}
        >
          <div
            className={`process-text-block process-animate-left ${isInView ? 'active' : ''}`}
            style={{ animationDelay: '0.4s' }}
          >
            <h3>{FEATURES[1].title}</h3>
            <p>{FEATURES[1].description}</p>
          </div>
        </div>

        {/* ── CENTER COLUMN: Funnel Model ────────────────── */}
        <div className="process-center-col">
          {/* The CSS 3D Funnel Model */}
          <div
            className={`process-animate-center ${isInView ? 'active' : ''}`}
            style={{ position: 'relative', zIndex: 2 }}
          >
            <FunnelModel />
          </div>
        </div>

        {/* ── RIGHT COLUMN: Feature 3 (top) & Feature 4 (bottom) ── */}
        <div
          style={{
            gridColumn: 3,
            gridRow: 1,
            alignSelf: 'center',
            paddingBottom: '30px',
          }}
        >
          <div
            className={`process-text-block process-animate-right ${isInView ? 'active' : ''}`}
            style={{ animationDelay: '0.2s' }}
          >
            <h3>{FEATURES[2].title}</h3>
            <p>{FEATURES[2].description}</p>
          </div>
        </div>

        <div
          style={{
            gridColumn: 3,
            gridRow: 2,
            alignSelf: 'center',
            paddingTop: '30px',
          }}
        >
          <div
            className={`process-text-block process-animate-right ${isInView ? 'active' : ''}`}
            style={{ animationDelay: '0.5s' }}
          >
            <h3>{FEATURES[3].title}</h3>
            <p>{FEATURES[3].description}</p>
          </div>
        </div>
      </div>

      {/* ── SVG Connection Lines (dashed lines from text to center) ── */}
      <svg
        className="process-connection-line"
        style={{
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          zIndex: 1,
        }}
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="lineGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="rgba(139, 92, 246, 0.3)" />
            <stop offset="100%" stopColor="rgba(139, 92, 246, 0)" />
          </linearGradient>
          <linearGradient id="lineGrad2" x1="100%" y1="0%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="rgba(139, 92, 246, 0.3)" />
            <stop offset="100%" stopColor="rgba(139, 92, 246, 0)" />
          </linearGradient>
        </defs>
      </svg>
    </section>
  );
}
