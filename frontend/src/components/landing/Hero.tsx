'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';

/* ────────────────────────────────────────────────────────────────────────────
   Icon Boxes — dark rounded squares with colored icons inside
   ──────────────────────────────────────────────────────────────────────────── */
function IconBox({ children, color = '#6366f1' }: { children: React.ReactNode; color?: string }) {
  return (
    <div style={{
      width: '48px',
      height: '48px',
      borderRadius: '8px',
      background: 'rgba(10, 14, 24, 0.95)',
      border: `1px solid ${color}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#ffffff', // Set text/icon color to white
      flexShrink: 0,
      position: 'relative', // Set relative positioning for absolute child overlay
      boxShadow: '0 0 25px rgba(0, 0, 0, 0.95), 0 12px 30px rgba(0, 0, 0, 0.95), inset 0 1px 0 rgba(255,255,255,0.08)', // Ambient all-around shadow + downward shadow
    }}>
      {/* Black shadow overlay overlapping the top side of the border */}
      <div style={{
        position: 'absolute',
        top: '-1px',
        left: '-1px',
        right: '-1px',
        height: '14px',
        background: 'linear-gradient(to bottom, rgba(0, 0, 0, 0.95), transparent)',
        borderRadius: '8px 8px 0 0',
        pointerEvents: 'none',
        zIndex: 2,
      }} />
      {children}
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────────────
   SVG Icons (matching reference style)
   ──────────────────────────────────────────────────────────────────────────── */
function ProtocolIcon1() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M3 12h18M3 7l3 5-3 5M21 7l-3 5 3 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function ProtocolIcon2() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="3.5" stroke="currentColor" strokeWidth="1.8" />
      <circle cx="12" cy="3" r="1.5" fill="currentColor" />
      <circle cx="12" cy="21" r="1.5" fill="currentColor" />
      <circle cx="3" cy="12" r="1.5" fill="currentColor" />
      <circle cx="21" cy="12" r="1.5" fill="currentColor" />
      <path d="M12 5.5v-1M12 19.5v-1M5.5 12h-1M19.5 12h-1" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}
function ProtocolIcon3() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M4 4h6l2 4-2 4h6l2 4-2 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function ProtocolIcon4() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" />
      <path d="M12 7v5l3.5 3.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function ProtocolIcon5() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function ProtocolIcon6() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.9 0 1.8-.1 2.6-.4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M22 12c0-2.4-.8-4.6-2.2-6.3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M15 9l3-3 3 3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M18 6v8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

/* ────────────────────────────────────────────────────────────────────────────
   HERO SECTION — matches the reference image exactly
   ──────────────────────────────────────────────────────────────────────────── */
export function HeroSection() {
  const router = useRouter();
  const { user } = useAuth();
  
  useEffect(() => {
    if (user) {
      router.push('/industrial');
    }
  }, [user, router]);

  const words = ["Clarity", "Confidence", "Control", "Velocity"];
  const [wordIndex, setWordIndex] = useState(0);
  const [currentText, setCurrentText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const currentWord = words[wordIndex];
    let timeoutId: NodeJS.Timeout;

    if (isDeleting) {
      if (currentText === "") {
        setIsDeleting(false);
        setWordIndex((prev) => (prev + 1) % words.length);
      } else {
        timeoutId = setTimeout(() => {
          setCurrentText(currentText.substring(0, currentText.length - 1));
        }, 50);
      }
    } else {
      if (currentText === currentWord) {
        timeoutId = setTimeout(() => {
          setIsDeleting(true);
        }, 2000);
      } else {
        timeoutId = setTimeout(() => {
          setCurrentText(currentWord.substring(0, currentText.length + 1));
        }, 100);
      }
    }

    return () => clearTimeout(timeoutId);
  }, [currentText, isDeleting, wordIndex, words]);

  return (
    <section style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
      paddingTop: '80px',
      paddingBottom: '0',
    }}>
      <style dangerouslySetInnerHTML={{
        __html: `
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(24px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes drawPath {
          to {
            stroke-dashoffset: 0;
          }
        }
        .hero-fade-in-1 {
          opacity: 0;
          animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          animation-delay: 0.1s;
        }
        .hero-fade-in-2 {
          opacity: 0;
          animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          animation-delay: 0.25s;
        }
        .hero-fade-in-card {
          opacity: 0;
          animation: fadeInUp 1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          animation-delay: 0.4s;
        }
        .draw-line-top {
          stroke-dasharray: 600;
          stroke-dashoffset: 600;
          animation: drawPath 2.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
          animation-delay: 0.9s;
        }
        .draw-line-bottom {
          stroke-dasharray: 800;
          stroke-dashoffset: 800;
          animation: drawPath 3.2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
          animation-delay: 1.5s;
        }
        .hero-pulse-group {
          opacity: 0;
          animation: fadeIn 0.5s ease-in forwards;
          animation-delay: 4.7s;
        }
        .fade-in-icons {
          opacity: 0;
          animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          animation-delay: 1.0s;
        }
        .fade-in-logo {
          opacity: 0;
          animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          animation-delay: 1.1s;
        }
        @media (min-width: 768px) and (max-width: 1023px) {
          .hero-fade-in-card {
            max-height: 410px !important;
            padding-top: 40px !important;
            padding-bottom: 24px !important;
          }
          .hero-integrations-container {
            width: 800px !important;
            left: 50% !important;
            transform: translate(-50%, 0) scale(0.75) !important;
            transform-origin: center top;
            margin-bottom: -60px;
          }
          .hero-integrations-container svg {
            transform: scaleY(1.3) !important;
            transform-origin: center top;
          }
        }
        @media (min-width: 1024px) {
          .hero-integrations-container svg {
            transform: scaleY(1.18) !important;
            transform-origin: center top;
          }
        }
        .desktop-svg {
          display: block !important;
        }
        .mobile-svg {
          display: none !important;
        }
        @media (max-width: 767px) {
          .desktop-svg {
            display: none !important;
          }
          .mobile-svg {
            display: block !important;
          }
          .hero-fade-in-card {
            height: 340px !important;
            max-height: 340px !important;
            padding: 24px 12px 16px !important;
          }
          .hero-fade-in-2 {
            margin-bottom: 8px !important;
          }
          .hero-integrations-container {
            width: 320px !important;
            max-width: 100% !important;
            height: 240px !important;
            transform: none !important;
            margin-top: 8px !important;
            margin-bottom: 0px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            overflow: visible !important;
          }
          .fade-in-logo {
            top: 40px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
          }
          .fade-in-icons {
            top: auto !important;
          }
          .icon-1 {
            top: 130px !important;
            left: calc(50% - 64px) !important;
            transform: translateX(-50%) !important;
          }
          .icon-2 {
            top: 130px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
          }
          .icon-3 {
            top: 130px !important;
            left: calc(50% + 64px) !important;
            transform: translateX(-50%) !important;
          }
          .icon-4 {
            top: 185px !important;
            left: calc(50% - 64px) !important;
            transform: translateX(-50%) !important;
          }
          .icon-5 {
            top: 185px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
          }
          .icon-6 {
            top: 185px !important;
            left: calc(50% + 64px) !important;
            transform: translateX(-50%) !important;
          }
        }
      `}} />

      {/* ── Purple atmospheric glow (matches reference bg) ─────────────── */}
      <div style={{
        position: 'absolute',
        top: '-10%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '140%',
        height: '80%',
        background: 'radial-gradient(ellipse 60% 50% at 50% 20%, rgba(100, 50, 180, 0.18) 0%, rgba(60, 20, 140, 0.08) 40%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute',
        top: '0',
        left: '30%',
        width: '40%',
        height: '60%',
        background: 'radial-gradient(ellipse at center, rgba(120, 60, 200, 0.1) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* ═══════════════════════════════════════════════════════════════════
          SPOTLIGHT EFFECT — 3D Dark Ceiling Trapezoid
          ═══════════════════════════════════════════════════════════════════ */}

      {/* Dark Ceiling / Top Area */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        background: '#04060c', // Matches the darkest part of the theme
        zIndex: 1,
        pointerEvents: 'none',
        // Adjusted the left point from -390px to -440px to move the left diagonal line outwards
        clipPath: 'polygon(10% 0, 90% 0, calc(50% + 450px) calc(50% - 150px), calc(50% - 450px) calc(50% - 150px))',
      }} />

      {/* Subtle border lines matching the diagonal cuts to give it that 3D room feel (optional but makes it look sharp) */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 2,
        pointerEvents: 'none',
        background: 'transparent',
        // We can use a pseudo-element or just rely on the sharp contrast.
        // The clip-path above creates a very sharp edge, which is what the user drew.
      }} />

      {/* ── Main hero card with colored border ─────────────────────────── */}
      <div style={{
        position: 'relative',
        width: '100%',
        maxWidth: '980px',
        margin: '0 24px',
        padding: '0 24px',
        zIndex: 3,
      }}>


        <div className="hero-fade-in-card" style={{
          position: 'relative',
          borderRadius: '12px', // Adjusted roundness (was 24px)
          padding: '56px 48px 40px',
          background: 'transparent',
          border: '1px solid #3f1495', // Vibrant purple border matching reference
          boxShadow: '0 50px 100px -20px rgba(0, 0, 0, 0.85), 0 40px 120px rgba(140, 80, 220, 0.15), inset 0 1px 0 rgba(255,255,255,0.02)', // Deep black background shadow added
          backdropFilter: 'blur(20px)',
          overflow: 'visible',
          maxHeight: '480px', // Reverted back to minHeight to prevent overflow!
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center', // Centers the content vertically
        }}>


          {/* ── Headline (serif italic, inside card) ───────────────────── */}
          <h1 className="hero-fade-in-1" style={{
            fontSize: 'clamp(36px, 5.5vw, 58px)',
            fontWeight: 700,
            lineHeight: 1.15,
            letterSpacing: '-0.01em',
            textAlign: 'center',
            color: 'var(--text-primary)',
            marginBottom: '4px',
            marginTop: 0,
          }}>
            Complexity Down,
          </h1>
          <h1 className="hero-fade-in-2" style={{
            fontSize: 'clamp(36px, 5.5vw, 58px)',
            fontWeight: 700,
            lineHeight: 1.15,
            letterSpacing: '-0.01em',
            textAlign: 'center',
            marginBottom: '36px',
            marginTop: 0,
          }}>
            <span style={{
              background: 'linear-gradient(135deg, #f97316 0%, #e05028 30%, #a855f7 70%, #7c3aed 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              display: 'inline-block',
            }}>
              {currentText}
              <span style={{
                color: '#a855f7',
                fontWeight: 300,
                WebkitTextFillColor: '#a855f7',
                animation: 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite'
              }}>|</span>
            </span>
            <style>{`
              @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0; }
              }
            `}</style>
            <span style={{ color: 'var(--text-primary)' }}> Up</span>
          </h1>

          {/* ── Integrations row & Routing Lines ──────────────────────────── */}
          <div className="hero-integrations-container" style={{
            width: '100%',
            maxWidth: '800px',
            margin: '0 auto',
            position: 'relative',
            height: '280px',
            marginTop: '12px'
          }}>

            {/* SVG Routing Lines */}
            <svg className="desktop-svg" width="800" height="280" style={{ position: 'absolute', top: 0, left: 0, zIndex: 0, overflow: 'visible' }}>
              <defs>
                {/* Glow filter for animated dots */}
                <filter id="hero-glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
                <linearGradient id="split-left" x1="400" y1="36" x2="250" y2="95" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stopColor="#ffffff" />
                  <stop offset="30%" stopColor="#a855f7" />
                  <stop offset="70%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="rgba(99, 102, 241, 0)" />
                </linearGradient>
                <linearGradient id="split-right" x1="400" y1="36" x2="550" y2="95" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stopColor="#ffffff" />
                  <stop offset="30%" stopColor="#a855f7" />
                  <stop offset="70%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="rgba(99, 102, 241, 0)" />
                </linearGradient>
              </defs>

              {/* 1. BLACK SHADOW UNDERLAYS FIRST (renders at the bottom of the stack) */}

              {/* Top Shadows */}
              <path className="draw-line-top" d="M 394 36 L 394 42 Q 390 52 379 52 L 300 52 Q 280 52 280 67 L 280 80 Q 280 95 260 95 L 50 95" stroke="#000000" strokeWidth="6" fill="none" opacity="0.9" transform="translate(0, 4)" style={{ filter: 'blur(3px)' }} />
              <path className="draw-line-top" d="M 406 36 L 406 42 Q 406 52 421 52 L 500 52 Q 520 52 520 67 L 520 80 Q 520 95 540 95 L 750 95" stroke="#000000" strokeWidth="6" fill="none" opacity="0.9" transform="translate(0, 4)" style={{ filter: 'blur(3px)' }} />

              {/* Bottom Shadows */}
              <path className="draw-line-bottom" d="M 90 113 L 90 188 Q 90 200 102 200 L 360 200 Q 372 200 372 212 L 372 340" stroke="#000000" strokeWidth="8" fill="none" opacity="0.95" transform="translate(0, 2)" style={{ filter: 'blur(4px)' }} />
              <path className="draw-line-bottom" d="M 160 113 L 160 192 Q 160 204 172 204 L 368 204 Q 380 204 380 216 L 380 340" stroke="#000000" strokeWidth="8" fill="none" opacity="0.95" transform="translate(0, 2)" style={{ filter: 'blur(4px)' }} />
              <path className="draw-line-bottom" d="M 230 113 L 230 196 Q 230 208 242 208 L 376 208 Q 388 208 388 220 L 388 340" stroke="#000000" strokeWidth="8" fill="none" opacity="0.95" transform="translate(0, 2)" style={{ filter: 'blur(4px)' }} />
              <path className="draw-line-bottom" d="M 570 113 L 570 196 Q 570 208 558 208 L 424 208 Q 412 208 412 220 L 412 340" stroke="#000000" strokeWidth="8" fill="none" opacity="0.95" transform="translate(0, 2)" style={{ filter: 'blur(4px)' }} />
              <path className="draw-line-bottom" d="M 640 113 L 640 192 Q 640 204 628 204 L 432 204 Q 420 204 420 216 L 420 340" stroke="#000000" strokeWidth="8" fill="none" opacity="0.95" transform="translate(0, 2)" style={{ filter: 'blur(4px)' }} />
              <path className="draw-line-bottom" d="M 710 113 L 710 188 Q 710 200 698 200 L 440 200 Q 428 200 428 212 L 428 340" stroke="#000000" strokeWidth="8" fill="none" opacity="0.95" transform="translate(0, 2)" style={{ filter: 'blur(4px)' }} />

              {/* 2. COLORED FOREGROUND LINES (renders on top of all shadows) */}

              {/* Top Lines */}
              <path className="draw-line-top" d="M 394 36 L 394 42 Q 390 52 379 52 L 300 52 Q 280 52 280 67 L 280 80 Q 280 95 260 95 L 50 95" stroke="url(#split-left)" strokeWidth="2" fill="none" />
              <path className="draw-line-top" d="M 406 36 L 406 42 Q 406 52 421 52 L 500 52 Q 520 52 520 67 L 520 80 Q 520 95 540 95 L 750 95" stroke="url(#split-right)" strokeWidth="2" fill="none" />

              {/* Bottom Lines */}
              <path className="draw-line-bottom" d="M 90 113 L 90 188 Q 90 200 102 200 L 360 200 Q 372 200 372 212 L 372 340" stroke="#e81cff" strokeWidth="1.5" fill="none" strokeLinejoin="round" opacity="0.6" />
              <path className="draw-line-bottom" d="M 160 113 L 160 192 Q 160 204 172 204 L 368 204 Q 380 204 380 216 L 380 340" stroke="#10b981" strokeWidth="1.5" fill="none" strokeLinejoin="round" opacity="0.6" />
              <path className="draw-line-bottom" d="M 230 113 L 230 196 Q 230 208 242 208 L 376 208 Q 388 208 388 220 L 388 340" stroke="#f97316" strokeWidth="1.5" fill="none" strokeLinejoin="round" opacity="0.6" />
              <path className="draw-line-bottom" d="M 570 113 L 570 196 Q 570 208 558 208 L 424 208 Q 412 208 412 220 L 412 340" stroke="#06b6d4" strokeWidth="1.5" fill="none" strokeLinejoin="round" opacity="0.6" />
              <path className="draw-line-bottom" d="M 640 113 L 640 192 Q 640 204 628 204 L 432 204 Q 420 204 420 216 L 420 340" stroke="#f59e0b" strokeWidth="1.5" fill="none" strokeLinejoin="round" opacity="0.6" />
              <path className="draw-line-bottom" d="M 710 113 L 710 188 Q 710 200 698 200 L 440 200 Q 428 200 428 212 L 428 340" stroke="#8b5cf6" strokeWidth="1.5" fill="none" strokeLinejoin="round" opacity="0.6" />

              {/* Animated Light Pulses */}
              <g className="hero-pulse-group">
                <g><animateMotion dur="3.2s" repeatCount="indefinite" path="M 90 113 L 90 188 Q 90 200 102 200 L 360 200 Q 372 200 372 212 L 372 340" begin="0s" /><circle r="4.5" fill="#e81cff" filter="url(#hero-glow)" /><circle r="1.5" fill="#fff" /></g>
                <g><animateMotion dur="2.7s" repeatCount="indefinite" path="M 160 113 L 160 192 Q 160 204 172 204 L 368 204 Q 380 204 380 216 L 380 340" begin="0.8s" /><circle r="4.5" fill="#10b981" filter="url(#hero-glow)" /><circle r="1.5" fill="#fff" /></g>
                <g><animateMotion dur="3.5s" repeatCount="indefinite" path="M 230 113 L 230 196 Q 230 208 242 208 L 376 208 Q 388 208 388 220 L 388 340" begin="1.4s" /><circle r="4.5" fill="#f97316" filter="url(#hero-glow)" /><circle r="1.5" fill="#fff" /></g>
                <g><animateMotion dur="2.9s" repeatCount="indefinite" path="M 570 113 L 570 196 Q 570 208 558 208 L 424 208 Q 412 208 412 220 L 412 340" begin="0.3s" /><circle r="4.5" fill="#06b6d4" filter="url(#hero-glow)" /><circle r="1.5" fill="#fff" /></g>
                <g><animateMotion dur="3.4s" repeatCount="indefinite" path="M 640 113 L 640 192 Q 640 204 628 204 L 432 204 Q 420 204 420 216 L 420 340" begin="1.1s" /><circle r="4.5" fill="#f59e0b" filter="url(#hero-glow)" /><circle r="1.5" fill="#fff" /></g>
                <g><animateMotion dur="3.1s" repeatCount="indefinite" path="M 710 113 L 710 188 Q 710 200 698 200 L 440 200 Q 428 200 428 212 L 428 340" begin="0.6s" /><circle r="4.5" fill="#8b5cf6" filter="url(#hero-glow)" /><circle r="1.5" fill="#fff" /></g>
              </g>
            </svg>

            {/* Mobile SVG Routing Lines */}
            <svg className="mobile-svg" width="320" height="280" style={{ position: 'absolute', top: 0, left: 0, zIndex: 0, overflow: 'visible', display: 'none' }}>
              <defs>
                <linearGradient id="split-left-mobile" x1="160" y1="36" x2="120" y2="48" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stopColor="#ffffff" />
                  <stop offset="30%" stopColor="#a855f7" />
                  <stop offset="100%" stopColor="rgba(99, 102, 241, 0)" />
                </linearGradient>
                <linearGradient id="split-right-mobile" x1="160" y1="36" x2="200" y2="48" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" stopColor="#ffffff" />
                  <stop offset="30%" stopColor="#a855f7" />
                  <stop offset="100%" stopColor="rgba(99, 102, 241, 0)" />
                </linearGradient>
              </defs>

              {/* 1. BLACK SHADOW UNDERLAYS */}
              <path className="draw-line-bottom" d="M 96 178 L 96 240 L 148 240 L 148 340" stroke="#000000" strokeWidth="5" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} />
              <path className="draw-line-bottom" d="M 160 178 L 160 240 L 152 240 L 152 340" stroke="#000000" strokeWidth="5" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} />
              <path className="draw-line-bottom" d="M 224 178 L 224 240 L 156 240 L 156 340" stroke="#000000" strokeWidth="5" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} />

              <path className="draw-line-bottom" d="M 96 233 L 96 248 L 164 248 L 164 340" stroke="#000000" strokeWidth="5" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} />
              <path className="draw-line-bottom" d="M 160 233 L 160 252 L 168 252 L 168 340" stroke="#000000" strokeWidth="5" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} />
              <path className="draw-line-bottom" d="M 224 233 L 224 248 L 172 248 L 172 340" stroke="#000000" strokeWidth="5" fill="none" opacity="0.9" style={{ filter: 'blur(3px)' }} />

              {/* 2. COLORED FOREGROUND LINES */}
              <path className="draw-line-bottom" d="M 96 178 L 96 240 L 148 240 L 148 340" stroke="#e81cff" strokeWidth="1.5" fill="none" />
              <path className="draw-line-bottom" d="M 160 178 L 160 240 L 152 240 L 152 340" stroke="#10b981" strokeWidth="1.5" fill="none" />
              <path className="draw-line-bottom" d="M 224 178 L 224 240 L 156 240 L 156 340" stroke="#f97316" strokeWidth="1.5" fill="none" />

              <path className="draw-line-bottom" d="M 96 233 L 96 248 L 164 248 L 164 340" stroke="#06b6d4" strokeWidth="1.5" fill="none" />
              <path className="draw-line-bottom" d="M 160 233 L 160 252 L 168 252 L 168 340" stroke="#f59e0b" strokeWidth="1.5" fill="none" />
              <path className="draw-line-bottom" d="M 224 233 L 224 248 L 172 248 L 172 340" stroke="#8b5cf6" strokeWidth="1.5" fill="none" />
            </svg>

            {/* Get a Demo Button */}
            <button style={{
              position: 'absolute',
              top: '0px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'white',
              color: 'black',
              borderRadius: '999px',
              padding: '8px 24px',
              fontWeight: 700,
              fontSize: '14px',
              border: 'none',
              cursor: 'pointer',
              zIndex: 10,
              boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 4px 14px rgba(255,255,255,0.15)'
            }}
            onClick={() => router.push('/login')}
            >
              Start Now
            </button>

            {/* Center Brand Area (overlapping the curves perfectly) */}
            <div className="fade-in-logo" style={{
              position: 'absolute', top: '76px', left: '400px', transform: 'translateX(-50%)',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', zIndex: 1
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{
                  width: '24px', height: '24px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <img src="/logo.png" alt="SureFlow" style={{ width: '20px', height: '20px', objectFit: 'contain' }} />
                </div>
                <span style={{
                  fontWeight: 800,
                  fontSize: '20px',
                  color: 'var(--text-primary)',
                  letterSpacing: '-0.02em',
                }}>
                  SureFlow
                </span>
              </div>
              <p style={{
                color: 'var(--text-secondary)',
                fontSize: '11px',
                textAlign: 'center',
                width: '200px',
                lineHeight: 1.4,
                margin: 0,
                fontWeight: 500,
              }}>
                SureFlow is a better way for your team to automate industrial operations.
              </p>
            </div>

            {/* Left Icons */}
            <div className="fade-in-icons icon-1" style={{ position: 'absolute', top: '65px', left: '90px', transform: 'translateX(-50%)', zIndex: 1 }}>
              <IconBox color="#e81cff"><ProtocolIcon1 /></IconBox>
            </div>
            <div className="fade-in-icons icon-2" style={{ position: 'absolute', top: '65px', left: '160px', transform: 'translateX(-50%)', zIndex: 1 }}>
              <IconBox color="#10b981"><ProtocolIcon2 /></IconBox>
            </div>
            <div className="fade-in-icons icon-3" style={{ position: 'absolute', top: '65px', left: '230px', transform: 'translateX(-50%)', zIndex: 1 }}>
              <IconBox color="#f97316"><ProtocolIcon3 /></IconBox>
            </div>

            {/* Right Icons */}
            <div className="fade-in-icons icon-4" style={{ position: 'absolute', top: '65px', left: '570px', transform: 'translateX(-50%)', zIndex: 1 }}>
              <IconBox color="#06b6d4"><ProtocolIcon4 /></IconBox>
            </div>
            <div className="fade-in-icons icon-5" style={{ position: 'absolute', top: '65px', left: '640px', transform: 'translateX(-50%)', zIndex: 1 }}>
              <IconBox color="#f59e0b"><ProtocolIcon5 /></IconBox>
            </div>
            <div className="fade-in-icons icon-6" style={{ position: 'absolute', top: '65px', left: '710px', transform: 'translateX(-50%)', zIndex: 1 }}>
              <IconBox color="#8b5cf6"><ProtocolIcon6 /></IconBox>
            </div>
          </div>
        </div>
      </div>

      {/* ── Full-width horizontal decorative line ──────────────────────── */}
      <div style={{
        width: '100%',
        maxWidth: '900px',
        height: '1px',
        background: 'linear-gradient(90deg, transparent, rgba(140, 80, 220, 0.3) 20%, rgba(255,255,255,0.08) 50%, rgba(249, 115, 22, 0.3) 80%, transparent)',
        marginTop: '0',
        marginBottom: '0',
      }} />
    </section>
  );
}