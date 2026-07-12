'use client';
import { useState, useEffect, useRef } from 'react';
import { Zap, Bell, Cpu, GitBranch, ShieldCheck, ArrowRight, Play, CheckCircle, AlertTriangle, Activity } from 'lucide-react';

type TabId = 'alerts' | 'integrations' | 'playbooks' | 'response';

interface TabConfig {
  id: TabId;
  label: string;
  icon: React.ComponentType<any>;
  title: string;
  description: string;
  color: string;
}

const TABS: TabConfig[] = [
  {
    id: 'alerts',
    label: 'Better Alerts',
    icon: Bell,
    title: 'What Makes a Better Alert?',
    description: 'A single screen that automatically compiles all the information you need to take decisive action, and groups related alerts so you only have to do it once.',
    color: '#8b5cf6', // purple
  },
  {
    id: 'integrations',
    label: 'Robust Integrations',
    icon: Cpu,
    title: 'Seamless Industrial Integration',
    description: 'Connect your entire operational technology (OT) and enterprise software stack in minutes. Out-of-the-box connectors unify telemetry across PLCs, SCADA, and ERPs.',
    color: '#06b6d4', // cyan
  },
  {
    id: 'playbooks',
    label: 'Brilliant Playbooks',
    icon: GitBranch,
    title: 'Automate with Precision',
    description: 'Build and deploy automated standard operating procedures (SOPs) with an intuitive flow. Resolve routine deviations instantly while keeping engineers in the loop.',
    color: '#f97316', // orange
  },
  {
    id: 'response',
    label: 'Faster Response',
    icon: ShieldCheck,
    title: 'Seconds, Not Hours',
    description: 'Execute rapid containment and mitigation protocols automatically. Trigger valve shutoffs, isolate faulty machinery, and dispatch repair logs instantly.',
    color: '#10b981', // green
  },
];

export function DetailSection() {
  const [activeTab, setActiveTab] = useState<TabId>('alerts');
  const [runTime, setRunTime] = useState<number>(0);
  const [isInView, setIsInView] = useState<boolean>(false);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setRunTime((prev) => (prev > 99 ? 0 : prev + 0.1));
    }, 100);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
        }
      },
      { threshold: 0.35 }
    );
    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }
    return () => {
      observer.disconnect();
    };
  }, []);

  const currentTab = TABS.find((t) => t.id === activeTab)!;
  const shouldAnimate = isInView;

  return (
    <section ref={sectionRef} style={{
      position: 'relative',
      background: 'var(--bg-primary)',
      paddingTop: '0px',
      paddingBottom: '120px',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    }}>
      <style dangerouslySetInnerHTML={{
        __html: `
          .tab-btn {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          }
          .tab-btn:hover {
            background: rgba(255, 255, 255, 0.03);
          }
          .glow-green {
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
          }
          .glow-cyan {
            box-shadow: 0 0 20px rgba(6, 118, 212, 0.15);
          }
          .glow-orange {
            box-shadow: 0 0 20px rgba(249, 115, 22, 0.15);
          }
          .glow-purple {
            box-shadow: 0 0 20px rgba(139, 92, 246, 0.15);
          }
          @keyframes borderGlow {
            0%, 100% { border-color: rgba(255, 255, 255, 0.06); }
            50% { border-color: var(--accent); }
          }
          .pulse-border {
            animation: borderGlow 4s ease infinite;
          }
          @keyframes pingSlow {
            0% { transform: scale(1); opacity: 1; }
            70%, 100% { transform: scale(2); opacity: 0; }
          }
          .ping-slow {
            animation: pingSlow 2s cubic-bezier(0.16, 1, 0.3, 1) infinite;
          }
          @keyframes drawLine {
            from {
              stroke-dashoffset: 2000;
            }
            to {
              stroke-dashoffset: 0;
            }
          }
          .animate-line {
            stroke-dasharray: 2000;
            stroke-dashoffset: 2000;
          }
          .animate-line.active {
            animation: drawLine 3.6s cubic-bezier(0.2, 0.85, 0.35, 1) forwards;
          }
          .animate-line.active.delay-inner {
            animation-delay: 0s;
          }
          .animate-line.active.delay-mid {
            animation-delay: 0.12s;
          }
          .animate-line.active.delay-outer {
            animation-delay: 0.24s;
          }
          .detail-lines-svg {
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            overflow: visible;
          }
          .detail-text-container {
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 900px;
          }
          .detail-svg-wrapper {
            position: relative;
            width: 100%;
            max-width: 1200px;
            height: 550px;
            z-index: 1;
          }
          @media (max-width: 1199px) {
            .detail-lines-svg {
              transform: translateX(-50%) scale(0.82);
              transform-origin: center top;
            }
            .detail-text-container {
              max-width: 740px;
            }
            .detail-svg-wrapper {
              height: 452px;
            }
          }
        `
      }} />

      {/* ── TOP SVG LINES: Center aligned to receive lines from TrustedBy ────────── */}
      <div className="detail-svg-wrapper">
        <svg width="1200" height="550" className="detail-lines-svg">
          {/* Black shadow lines underneath for premium contrast */}
          <path d="M 572 0 L 572 20 Q 572 50 542 50 L 110 50 Q 80 50 80 80 L 80 550" stroke="#000000" strokeWidth="6" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} className={`animate-line ${shouldAnimate ? 'active' : ''} delay-outer`} />
          <path d="M 580 0 L 580 24 Q 580 54 550 54 L 120 54 Q 90 54 90 84 L 90 550" stroke="#000000" strokeWidth="6" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} className={`animate-line ${shouldAnimate ? 'active' : ''} delay-mid`} />
          <path d="M 588 0 L 588 28 Q 588 58 558 58 L 130 58 Q 100 58 100 88 L 100 550" stroke="#000000" strokeWidth="6" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} className={`animate-line ${shouldAnimate ? 'active' : ''} delay-inner`} />

          <path d="M 612 0 L 612 28 Q 612 58 642 58 L 1070 58 Q 1100 58 1100 88 L 1100 550" stroke="#000000" strokeWidth="6" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} className={`animate-line ${shouldAnimate ? 'active' : ''} delay-inner`} />
          <path d="M 620 0 L 620 24 Q 620 54 650 54 L 1080 54 Q 1110 54 1110 84 L 1110 550" stroke="#000000" strokeWidth="6" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} className={`animate-line ${shouldAnimate ? 'active' : ''} delay-mid`} />
          <path d="M 628 0 L 628 20 Q 628 50 658 50 L 1090 50 Q 1120 50 1120 80 L 1120 550" stroke="#000000" strokeWidth="6" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} className={`animate-line ${shouldAnimate ? 'active' : ''} delay-outer`} />

          {/* Left Group - Base Colored Lines */}
          <path d="M 572 0 L 572 20 Q 572 50 542 50 L 110 50 Q 80 50 80 80 L 80 550" stroke="#e81cff" strokeWidth="1.5" fill="none" opacity="0.7" className={`animate-line ${shouldAnimate ? 'active' : ''} delay-outer`} />
          <path d="M 580 0 L 580 24 Q 580 54 550 54 L 120 54 Q 90 54 90 84 L 90 550" stroke="#10b981" strokeWidth="1.5" fill="none" opacity="0.7" className={`animate-line ${shouldAnimate ? 'active' : ''} delay-mid`} />
          <path d="M 588 0 L 588 28 Q 588 58 558 58 L 130 58 Q 100 58 100 88 L 100 550" stroke="#f97316" strokeWidth="1.5" fill="none" opacity="0.7" className={`animate-line ${shouldAnimate ? 'active' : ''} delay-inner`} />

          {/* Right Group - Base Colored Lines */}
          <path d="M 612 0 L 612 28 Q 612 58 642 58 L 1070 58 Q 1100 58 1100 88 L 1100 550" stroke="#06b6d4" strokeWidth="1.5" fill="none" opacity="0.7" className={`animate-line ${shouldAnimate ? 'active' : ''} delay-inner`} />
          <path d="M 620 0 L 620 24 Q 620 54 650 54 L 1080 54 Q 1110 54 1110 84 L 1110 550" stroke="#f59e0b" strokeWidth="1.5" fill="none" opacity="0.7" className={`animate-line ${shouldAnimate ? 'active' : ''} delay-mid`} />
          <path d="M 628 0 L 628 20 Q 628 50 658 50 L 1090 50 Q 1120 50 1120 80 L 1120 550" stroke="#8b5cf6" strokeWidth="1.5" fill="none" opacity="0.7" className={`animate-line ${shouldAnimate ? 'active' : ''} delay-outer`} />
        </svg>

        {/* ── Central Text Content (framed by the lines) ──────────────── */}
        <div className="detail-text-container" style={{
          position: 'absolute',
          top: '195px',
          textAlign: 'center',
          zIndex: 2,
        }}>
          <h2 style={{
            fontSize: 'clamp(36px, 7vw, 44px)',
            fontWeight: 800,
            lineHeight: 1.2,
            letterSpacing: '-0.02em',
            margin: '0 0 16px 0',
            color: 'var(--text-primary)',
          }}>
            The Automation{' '}
            <span style={{
              background: 'linear-gradient(135deg, #f97316 0%, #e05028 30%, #a855f7 70%, #7c3aed 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}>
              Industrial Operations
            </span>{' '}
            Need
          </h2>
          <p style={{
            color: 'var(--text-secondary)',
            fontSize: '15px',
            lineHeight: 1.65,
            maxWidth: '640px',
            margin: '0 auto',
            fontWeight: 400,
          }}>
            With every element designed for the purpose of making the lives of operations pros easier,
            SureFlow combines an intuitive, single pane of glass with profoundly effective features.
          </p>
        </div>
      </div>

      {/* ── TABS BAR (Aligns perfectly with the bottom of the SVG lines) ── */}
      <div style={{
        width: '100%',
        maxWidth: '1200px',
        padding: '0 20px',
        zIndex: 5,
        marginTop: '-1px', // overlaps the lines nicely
      }}>
        <div style={{
          background: 'rgba(10, 14, 24, 0.85)',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          overflow: 'hidden',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255,255,255,0.03)',
        }} className="pulse-border">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="tab-btn"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '16px 8px',
                  border: 'none',
                  background: isActive ? `linear-gradient(to bottom, rgba(255,255,255,0.03), rgba(255,255,255,0)) font-box` : 'transparent',
                  borderBottom: isActive ? `2px solid ${tab.color}` : '2px solid transparent',
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '14px',
                  outline: 'none',
                }}
              >
                <Icon size={16} style={{ color: isActive ? tab.color : 'inherit', transition: 'color 0.2s' }} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── DETAIL DISPLAY PANEL (Content + Interactive Mockups) ────────── */}
      <div style={{
        width: '100%',
        maxWidth: '980px',
        margin: '48px auto 0',
        padding: '0 24px',
        zIndex: 5,
        display: 'grid',
        gridTemplateColumns: '1fr',
      }}>
        <div style={{
          background: 'rgba(10, 14, 24, 0.7)',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          padding: '40px',
          backdropFilter: 'blur(20px)',
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.1fr) minmax(0, 1.4fr)',
          gap: '48px',
          alignItems: 'center',
          boxShadow: '0 40px 80px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255,255,255,0.02)',
        }} className={`
          ${activeTab === 'alerts' ? 'glow-green' : ''}
          ${activeTab === 'integrations' ? 'glow-cyan' : ''}
          ${activeTab === 'playbooks' ? 'glow-orange' : ''}
          ${activeTab === 'response' ? 'glow-purple' : ''}
        `}>
          {/* Left Column: Descriptions */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h3 style={{
              fontSize: 'clamp(20px, 3.5vw, 28px)',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
              letterSpacing: '-0.01em',
            }}>
              {currentTab.title}
            </h3>
            <p style={{
              fontSize: '14px',
              color: 'var(--text-secondary)',
              lineHeight: 1.65,
              margin: 0,
            }}>
              {currentTab.description}
            </p>
            <div>
              <button style={{
                background: currentTab.color,
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: 600,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                boxShadow: `0 8px 20px -4px ${currentTab.color}80`,
              }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-1px)';
                  e.currentTarget.style.boxShadow = `0 12px 24px -2px ${currentTab.color}cc`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = `0 8px 20px -4px ${currentTab.color}80`;
                }}
              >
                <span>Learn More</span>
                <ArrowRight size={15} />
              </button>
            </div>
          </div>

          {/* Right Column: Visual Mockup Showcase */}
          <div style={{
            position: 'relative',
            width: '100%',
            height: '280px',
            background: 'rgba(5, 8, 16, 0.95)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '12px',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
          }}>
            {/* Window chrome / dots */}
            <div style={{
              height: '32px',
              background: 'rgba(255,255,255,0.02)',
              borderBottom: '1px solid rgba(255,255,255,0.04)',
              display: 'flex',
              alignItems: 'center',
              padding: '0 12px',
              gap: '6px',
            }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }} />
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#fbbf24' }} />
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }} />
              <span style={{ marginLeft: '12px', fontSize: '10px', color: 'rgba(255,255,255,0.3)', fontFamily: 'monospace' }}>
                sureflow_os::{activeTab}_terminal
              </span>
            </div>

            {/* Content Switcher */}
            <div style={{ height: 'calc(100% - 32px)', padding: '16px', overflow: 'hidden' }}>
              {activeTab === 'alerts' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', height: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600 }}>Active Incident Inbox</span>
                    <span style={{ fontSize: '10px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                      12 Pending
                    </span>
                  </div>

                  {/* Alert Card 1 */}
                  <div style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    borderRadius: '8px',
                    padding: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    position: 'relative',
                  }}>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: '#ef4444',
                      boxShadow: '0 0 8px #ef4444',
                    }} className="ping-slow" />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>Centrifugal Pump Temperature Spike</div>
                      <div style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>ID: #SF-PUMP-02 • Value: 94.6°C (Threshold: 80°C)</div>
                    </div>
                    <span style={{ fontSize: '10px', color: '#ef4444', fontWeight: 600, background: 'rgba(239,68,68,0.08)', padding: '2px 6px', borderRadius: '4px' }}>
                      CRITICAL
                    </span>
                  </div>

                  {/* Alert Card 2 */}
                  <div style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid rgba(245, 158, 11, 0.15)',
                    borderRadius: '8px',
                    padding: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                  }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>Inlet Valve Flow Rate Fluctuation</div>
                      <div style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>ID: #SF-VALVE-09 • Value: 12.4 L/s (Target: 15 L/s)</div>
                    </div>
                    <span style={{ fontSize: '10px', color: '#f59e0b', fontWeight: 600, background: 'rgba(245,158,11,0.08)', padding: '2px 6px', borderRadius: '4px' }}>
                      WARNING
                    </span>
                  </div>

                  {/* Auto-Correlation Footer */}
                  <div style={{
                    marginTop: 'auto',
                    background: 'rgba(16, 185, 129, 0.05)',
                    border: '1px dashed rgba(16, 185, 129, 0.2)',
                    borderRadius: '6px',
                    padding: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '10px',
                    color: '#10b981',
                  }}>
                    <CheckCircle size={12} />
                    <span>AI Engine auto-grouped 4 matching anomalies under turbine telemetry.</span>
                  </div>
                </div>
              )}

              {activeTab === 'integrations' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', justifyContent: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-around', position: 'relative' }}>
                    {/* Visual integration connector line */}
                    <div style={{
                      position: 'absolute',
                      top: '50%',
                      left: '10%',
                      right: '10%',
                      height: '2px',
                      background: 'linear-gradient(90deg, #10b981, #06b6d4, #8b5cf6)',
                      zIndex: 0,
                    }} />

                    {/* Source Node */}
                    <div style={{
                      zIndex: 1,
                      background: 'rgba(10, 14, 24, 0.95)',
                      border: '1px solid #10b981',
                      borderRadius: '8px',
                      padding: '8px 12px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '4px',
                      width: '90px',
                    }}>
                      <Cpu size={18} color="#10b981" />
                      <span style={{ fontSize: '9px', fontWeight: 600, color: 'var(--text-primary)' }}>PLC Modbus</span>
                      <span style={{ fontSize: '8px', color: '#10b981' }}>Live Streaming</span>
                    </div>

                    {/* Central Engine Node */}
                    <div style={{
                      zIndex: 1,
                      background: '#0d1525',
                      border: '2px solid #06b6d4',
                      borderRadius: '12px',
                      padding: '12px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '6px',
                      width: '110px',
                      boxShadow: '0 0 15px rgba(6, 182, 212, 0.3)',
                    }}>
                      <Zap size={22} color="#06b6d4" fill="#06b6d4" />
                      <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)' }}>SUREFLOW</span>
                      <span style={{ fontSize: '8px', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Central Router</span>
                    </div>

                    {/* Target Node */}
                    <div style={{
                      zIndex: 1,
                      background: 'rgba(10, 14, 24, 0.95)',
                      border: '1px solid #8b5cf6',
                      borderRadius: '8px',
                      padding: '8px 12px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '4px',
                      width: '90px',
                    }}>
                      <Activity size={18} color="#8b5cf6" />
                      <span style={{ fontSize: '9px', fontWeight: 600, color: 'var(--text-primary)' }}>SCADA HMI</span>
                      <span style={{ fontSize: '8px', color: '#8b5cf6' }}>Synchronized</span>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginTop: '10px' }}>
                    {['Slack Alert Gateway', 'SAP Work Order API', 'AWS Cloud Telemetry'].map((name, i) => (
                      <div key={i} style={{
                        background: 'rgba(255,255,255,0.02)',
                        border: '1px solid rgba(255,255,255,0.06)',
                        borderRadius: '6px',
                        padding: '6px',
                        fontSize: '9px',
                        textAlign: 'center',
                        color: 'var(--text-secondary)',
                      }}>
                        ✅ {name}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'playbooks' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', height: '100%', justifyContent: 'center' }}>
                  {/* Step 1 */}
                  <div style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid rgba(249,115,22,0.3)',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Play size={12} color="#f97316" fill="#f97316" />
                      <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-primary)' }}>Trigger: Temp Exceeds 80°C</span>
                    </div>
                    <span style={{ fontSize: '9px', color: '#f97316', fontWeight: 600 }}>Active</span>
                  </div>

                  {/* Flow Arrow */}
                  <div style={{ display: 'flex', justifyContent: 'center' }}>
                    <div style={{ width: '2px', height: '12px', background: 'rgba(249,115,22,0.4)' }} />
                  </div>

                  {/* Step 2 */}
                  <div style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <CheckCircle size={12} color="#10b981" />
                      <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-primary)' }}>Action: Enrich Diagnostic Telemetry</span>
                    </div>
                    <span style={{ fontSize: '9px', color: '#10b981' }}>Done</span>
                  </div>

                  {/* Flow Arrow */}
                  <div style={{ display: 'flex', justifyContent: 'center' }}>
                    <div style={{ width: '2px', height: '12px', background: 'rgba(255,255,255,0.1)' }} />
                  </div>

                  {/* Step 3 (Branching) */}
                  <div style={{
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <AlertTriangle size={12} color="#f59e0b" />
                      <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-primary)' }}>Condition: Operator Acknowledged?</span>
                    </div>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <span style={{ fontSize: '9px', background: 'rgba(16,185,129,0.15)', color: '#10b981', padding: '1px 4px', borderRadius: '3px' }}>Yes (Bypass)</span>
                      <span style={{ fontSize: '9px', background: 'rgba(239,68,68,0.15)', color: '#ef4444', padding: '1px 4px', borderRadius: '3px' }}>No (Escalate)</span>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'response' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', height: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', fontFamily: 'monospace' }}>TELEMETRY EVENT STREAM</span>
                    <span style={{ fontSize: '10px', color: '#8b5cf6', fontFamily: 'monospace' }}>
                      TIMELAPSE: {runTime.toFixed(1)}s
                    </span>
                  </div>

                  {/* Terminal log lines */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontFamily: 'monospace', fontSize: '10px' }}>
                    <div style={{ color: '#ef4444' }}>
                      [13:42:01] ⚠️ ALERT: Critical vibration threshold exceeded on Turbine #04
                    </div>
                    <div style={{ color: '#94a3b8' }}>
                      [13:42:02] ℹ️ INFERENCE: High wear signature matched bearing anomaly (94% confidence)
                    </div>
                    <div style={{ color: '#8b5cf6' }}>
                      [13:42:03] ⚡ PLAYBOOK: Triggering Cooldown Cycle #12 ...
                    </div>
                    <div style={{ color: '#10b981' }}>
                      [13:42:05] ✅ MITIGATION: Solenoid emergency valve closed. Cooldown initiated.
                    </div>
                    <div style={{ color: '#06b6d4' }}>
                      [13:42:08] 🚀 DISPATCH: SAP PM Work Order #WO-49291 auto-generated for repair team.
                    </div>
                  </div>

                  {/* Status Banner */}
                  <div style={{
                    marginTop: 'auto',
                    background: 'rgba(139, 92, 246, 0.1)',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                    borderRadius: '6px',
                    padding: '8px',
                    textAlign: 'center',
                    fontSize: '11px',
                    fontWeight: 600,
                    color: '#a78bfa',
                  }}>
                    🛡️ Operations Containment Achieved in 7.0 Seconds
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
