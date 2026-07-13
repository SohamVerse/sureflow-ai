'use client';
import { useEffect, useRef, useState } from 'react';

export function SecurityAutomation() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [isInView, setIsInView] = useState(false);
  const [animationKey, setAnimationKey] = useState(0);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          // Increment key to force remount of animated elements → restarts animation
          setAnimationKey((k) => k + 1);
          setIsInView(true);
        } else {
          setIsInView(false);
        }
      },
      { threshold: 0.35 }
    );
    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }
    return () => observer.disconnect();
  }, []);

  // SVG Paths for the 6 converging colored circuit traces (Double-Step Staircase, shortened at the end)
  const PATHS = {
    // Left paths
    pink: "M 100,0 L 100,10 Q 100,20 110,20 L 185,20 Q 200,20 210,30 L 260,80 Q 270,90 285,90 L 325,90 Q 340,90 350,100 L 400,150 Q 410,160 425,160 L 465,160 Q 480,160 480,175 L 480,200",
    cyan: "M 120,0 L 120,20 Q 120,35 135,35 L 190,35 Q 205,35 215,45 L 260,90 Q 270,100 285,100 L 325,100 Q 340,100 350,110 L 398,158 Q 408,168 423,168 L 473,168 Q 488,168 488,183 L 488,200",
    green: "M 140,0 L 140,35 Q 140,50 155,50 L 195,50 Q 210,50 220,60 L 260,100 Q 270,110 285,110 L 325,110 Q 340,110 350,120 L 396,166 Q 406,176 421,176 L 481,176 Q 496,176 496,191 L 496,200",
    // Right paths
    yellow: "M 900,0 L 900,10 Q 900,20 890,20 L 815,20 Q 800,20 790,30 L 740,80 Q 730,90 715,90 L 675,90 Q 660,90 650,100 L 600,150 Q 590,160 575,160 L 535,160 Q 520,160 520,175 L 520,200",
    orange: "M 880,0 L 880,20 Q 880,35 865,35 L 810,35 Q 795,35 785,45 L 740,90 Q 730,100 715,100 L 675,100 Q 660,100 650,110 L 602,158 Q 592,168 577,168 L 527,168 Q 512,168 512,183 L 512,200",
    purple: "M 860,0 L 860,35 Q 860,50 845,50 L 805,50 Q 790,50 780,60 L 740,100 Q 730,110 715,110 L 675,110 Q 660,110 650,120 L 604,166 Q 594,176 579,176 L 519,176 Q 504,176 504,191 L 504,200",
    // Background structural guidelines (Inner guidelines, below the active colored lines)
    bgLeft: "M 160,0 L 160,50 Q 160,65 175,65 L 200,65 Q 215,65 225,75 L 265,115 Q 270,120 285,120 L 325,120 Q 340,120 350,130 L 394,174 Q 404,184 419,184 L 441,184 Q 456,184 456,199 L 456,200",
    bgRight: "M 840,0 L 840,50 Q 840,65 825,65 L 800,65 Q 785,65 775,75 L 735,115 Q 730,120 715,120 L 675,120 Q 660,120 650,130 L 606,174 Q 596,184 581,184 L 559,184 Q 544,184 544,199 L 544,200",
    frameLeft: "M 80,0 Q 80,5 85,5 L 160,5 Q 175,5 185,15 L 225,55 Q 250,80 265,80 L 305,80 Q 320,80 330,90 L 372,132 Q 392,152 407,152 L 425,152 Q 440,152 440,167 L 440,200",
    frameRight: "M 920,0 Q 920,5 915,5 L 840,5 Q 825,5 815,15 L 775,55 Q 750,80 735,80 L 695,80 Q 680,80 670,90 L 628,132 Q 608,152 593,152 L 575,152 Q 560,152 560,167 L 560,200",
  };

  return (
    <section
      ref={sectionRef}
      className={`sec-auto-section ${isInView ? 'sec-in-view' : ''}`}
    >
      <style
        dangerouslySetInnerHTML={{
          __html: `
          .sec-auto-section {
            position: relative;
            background: var(--bg-primary);
            padding: 60px 0 60px 0;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100%;
          }

          /* ── Content Container ── */
          .sec-auto-container {
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 2;
          }

          /* ── Subtitle Label ── */
          .sec-auto-label {
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: #8b5cf6; /* security automation purple */
            margin-bottom: 20px;
            text-align: center;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.1s;
          }

          /* ── Main Title Heading ── */
          .sec-auto-title {
            font-size: 46px;
            font-weight: 800;
            line-height: 1.25;
            color: var(--text-primary);
            text-align: center;
            max-width: 800px;
            margin: 0 auto 24px auto;
            letter-spacing: -0.015em;
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.2s;
          }

          /* ── Empowers Gradient Text ── */
          .sec-auto-empowers {
            background: linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #f97316 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: inline-block;
          }

          /* ── Description Paragraph ── */
          .sec-auto-desc {
            font-size: 16px;
            line-height: 1.75;
            color: var(--text-secondary);
            text-align: center;
            max-width: 760px;
            margin: 0 auto 30px auto;
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.3s;
          }

          /* ── SVG Wires Section ── */
          .sec-auto-svg-wrap {
            width: 100%;
            max-width: 960px;
            margin: 0 auto;
            opacity: 0;
            transform: scale(0.96);
            transition: all 1s cubic-bezier(0.16, 1, 0.3, 1) 0.4s;
          }

          .sec-auto-svg {
            display: block;
            width: 100%;
            height: auto;
          }

          @keyframes drawSecLine {
            from {
              stroke-dashoffset: 2000;
            }
            to {
              stroke-dashoffset: 0;
            }
          }

          .sec-auto-line {
            stroke-dasharray: 2000;
            stroke-dashoffset: 2000;
          }

          .sec-auto-line.active {
            animation: drawSecLine 4.5s cubic-bezier(0.2, 0.85, 0.35, 1) forwards;
          }

          .sec-auto-pulse-group {
            opacity: 0;
            transition: opacity 0.5s ease-in 4.2s;
          }

          .sec-auto-pulse-group.active {
            opacity: 1;
          }

          /* ── Bottom Section Heading ── */
          .sec-auto-bottom-title {
            font-size: 34px;
            font-weight: 800;
            line-height: 1.35;
            color: var(--text-primary);
            text-align: center;
            max-width: 850px;
            margin: 30px auto 0 auto;
            letter-spacing: -0.01em;
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.6s;
          }

          .sec-auto-maximize {
            color: #8b5cf6;
          }

          /* ── Entrance States ── */
          .sec-in-view .sec-auto-label,
          .sec-in-view .sec-auto-title,
          .sec-in-view .sec-auto-desc,
          .sec-in-view .sec-auto-svg-wrap,
          .sec-in-view .sec-auto-bottom-title {
            opacity: 1;
            transform: translateY(0) scale(1);
          }

          /* ── Responsive Styling ── */
          @media (max-width: 900px) {
            .sec-auto-section {
              padding: 80px 0 90px 0;
            }
            .sec-auto-title {
              font-size: 34px;
            }
            .sec-auto-bottom-title {
              font-size: 26px;
              margin-top: 40px;
            }
            .sec-auto-desc {
              font-size: 15px;
              margin-bottom: 35px;
            }
          }
          @media (max-width: 600px) {
            .sec-auto-title {
              font-size: 28px;
            }
            .sec-auto-bottom-title {
              font-size: 20px;
            }
          }
        `,
        }}
      />

      <div className="sec-auto-container">
        {/* Subtitle */}
        <div className="sec-auto-label">Security Automation</div>

        {/* Main Title */}
        <h2 className="sec-auto-title">
          Automation that <span className="sec-auto-empowers">Empowers</span> SOC People and SOC Tools
        </h2>

        {/* Description */}
        <p className="sec-auto-desc">
          Everyone wants faster detection and response, but with the limited resources available to most security teams,
          this cannot be achieved without automation. Our Smart SOAR platform makes it easy to integrate your tools
          and turn them into a unified, automation-powered ecosystem.
        </p>

        <div className="sec-auto-svg-wrap">
          <svg
            className="sec-auto-svg"
            viewBox="0 0 1000 210"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              {/* Drop shadow for the entire active lines bundle to give depth without muddy overlaps */}
              <filter id="group-shadow" x="-10%" y="-10%" width="120%" height="120%">
                <feDropShadow dx="0" dy="5" stdDeviation="4" floodColor="#000000" floodOpacity="0.9" />
              </filter>

              {/* Pulsing Light Glow Filter for animated pulse circles */}
              <filter id="svg-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>

              {/* Linear Fade Mask for Left and Right edges */}
              <linearGradient id="fade-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="black" />
                <stop offset="12%" stopColor="white" />
                <stop offset="88%" stopColor="white" />
                <stop offset="100%" stopColor="black" />
              </linearGradient>

              <mask id="circuit-mask">
                <rect width="1000" height="210" fill="url(#fade-grad)" />
              </mask>
            </defs>

            {/* All animated lines — key forces remount on every viewport entry, restarting animations */}
            {isInView && (
              <g key={animationKey}>
                {/* Background structural lines */}
                <path
                  className="sec-auto-line active"
                  d={PATHS.bgLeft}
                  stroke="rgba(255, 255, 255, 0.18)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  className="sec-auto-line active"
                  d={PATHS.bgRight}
                  stroke="rgba(255, 255, 255, 0.18)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  className="sec-auto-line active"
                  d={PATHS.frameLeft}
                  stroke="rgba(255, 255, 255, 0.18)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  className="sec-auto-line active"
                  d={PATHS.frameRight}
                  stroke="rgba(255, 255, 255, 0.18)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                {/* Circuit Group with Mask */}
                <g mask="url(#circuit-mask)">

                  {/* Active colored lines */}
                  <g filter="url(#group-shadow)">
                    <path className="sec-auto-line active" d={PATHS.pink}   stroke="#ec4899" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
                    <path className="sec-auto-line active" d={PATHS.cyan}   stroke="#06b6d4" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
                    <path className="sec-auto-line active" d={PATHS.green}  stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
                    <path className="sec-auto-line active" d={PATHS.yellow} stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
                    <path className="sec-auto-line active" d={PATHS.orange} stroke="#ef4444" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
                    <path className="sec-auto-line active" d={PATHS.purple} stroke="#8b5cf6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
                  </g>

                  {/* Animated Light Pulses — delayed so they appear after lines finish drawing */}
                  <g className="sec-auto-pulse-group active">
                    <g><animateMotion dur="3.2s" repeatCount="indefinite" path={PATHS.pink}   begin="0s"   /><circle r="5.5" fill="#ec4899" opacity="0.75" filter="url(#svg-glow)" /><circle r="2" fill="#fff" /></g>
                    <g><animateMotion dur="2.7s" repeatCount="indefinite" path={PATHS.cyan}   begin="0.8s" /><circle r="5.5" fill="#06b6d4" opacity="0.75" filter="url(#svg-glow)" /><circle r="2" fill="#fff" /></g>
                    <g><animateMotion dur="3.5s" repeatCount="indefinite" path={PATHS.green}  begin="1.4s" /><circle r="5.5" fill="#10b981" opacity="0.75" filter="url(#svg-glow)" /><circle r="2" fill="#fff" /></g>
                    <g><animateMotion dur="2.9s" repeatCount="indefinite" path={PATHS.yellow} begin="0.3s" /><circle r="5.5" fill="#f59e0b" opacity="0.75" filter="url(#svg-glow)" /><circle r="2" fill="#fff" /></g>
                    <g><animateMotion dur="3.4s" repeatCount="indefinite" path={PATHS.orange} begin="1.1s" /><circle r="5.5" fill="#ef4444" opacity="0.75" filter="url(#svg-glow)" /><circle r="2" fill="#fff" /></g>
                    <g><animateMotion dur="3.1s" repeatCount="indefinite" path={PATHS.purple} begin="0.6s" /><circle r="5.5" fill="#8b5cf6" opacity="0.75" filter="url(#svg-glow)" /><circle r="2" fill="#fff" /></g>
                  </g>

                </g>
              </g>
            )}
          </svg>
        </div>

        {/* Bottom Headline */}
        <h3 className="sec-auto-bottom-title">
          <span className="sec-auto-maximize">Maximize</span> Your Technology Investments with Cybersecurity Automation
        </h3>
      </div>
    </section>
  );
}
