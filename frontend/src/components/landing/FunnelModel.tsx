'use client';

/**
 * FunnelModel — A 4-layer hollow 3D cylinder funnel.
 *
 * ClipPath Geometry:
 *   - The top edge curves downward (following the top rim ellipse).
 *   - The left and right side walls are straight vertical lines running 100% of the height.
 *   - The bottom edge curves upward (following the bottom rim ellipse), allowing cubes to exit cleanly.
 *   - This matches the ellipse center lines perfectly without leaving any visual gaps on the sides.
 */
export function FunnelModel() {
  return (
    <div className="fm-root">
      <style dangerouslySetInnerHTML={{ __html: FM_CSS }} />

      {/* ── Hidden SVG ClipPath Definition ────────────── */}
      <svg width="0" height="0" style={{ position: 'absolute', width: 0, height: 0 }}>
        <defs>
          <clipPath id="fm-cyl-clip" clipPathUnits="objectBoundingBox">
            <path d="M 0,0 Q 0.5,0.4 1,0 L 1,1 Q 0.5,0.6 0,1 Z" />
          </clipPath>
        </defs>
      </svg>

      {/* ── Large subtle background circle ────────────── */}
      <div className="fm-bg-circle" />

      {/* ── Subtle vertical lines in background ───────── */}
      <div className="fm-bg-lines">
        <div className="fm-bg-line fm-bg-line-l" />
        <div className="fm-bg-line fm-bg-line-r" />
      </div>

      {/* ── Cylinder Backs (z-index: 1) ───────────────── */}
      <div className="fm-layer fm-layer-1 fm-layer-back-only">
        <div className="fm-cylinder-back" />
      </div>
      <div className="fm-layer fm-layer-2 fm-layer-back-only">
        <div className="fm-cylinder-back" />
      </div>
      <div className="fm-layer fm-layer-3 fm-layer-back-only">
        <div className="fm-cylinder-back" />
      </div>
      <div className="fm-layer fm-layer-4 fm-layer-back-only">
        <div className="fm-cylinder-back" />
      </div>

      {/* ── Global Cubes Stream (z-index: 2) ───────────── */}
      <div className="fm-global-cubes">
        {GLOBAL_CUBES.map((c, i) => (
          <div
            key={i}
            className={`fm-cube ${c.cls}`}
            style={{
              animationName: c.anim,
              animationDelay: c.delay,
              animationDuration: c.dur,
            }}
          />
        ))}
      </div>

      {/* ── Cylinder Fronts (z-index: 3) ──────────────── */}
      <div className="fm-layer fm-layer-1">
        <div className="fm-cylinder-front">
          <div className="fm-top-rim" />
          <div className="fm-front-body" />
          <div className="fm-bottom-rim" />
        </div>
      </div>

      <div className="fm-layer fm-layer-2">
        <div className="fm-cylinder-front">
          <div className="fm-top-rim" />
          <div className="fm-front-body" />
          <div className="fm-bottom-rim" />
        </div>
      </div>

      <div className="fm-layer fm-layer-3">
        <div className="fm-cylinder-front">
          <div className="fm-top-rim" />
          <div className="fm-front-body" />
          <div className="fm-bottom-rim" />
        </div>
      </div>

      <div className="fm-layer fm-layer-4">
        <div className="fm-cylinder-front">
          <div className="fm-top-rim" />
          <div className="fm-front-body" />
          <div className="fm-bottom-rim" />
        </div>
      </div>

      {/* ── Bottom glow ellipse ────────────────────────── */}
      <div className="fm-bottom-glow">
        <div className="fm-bottom-glow-ring" />
        <div className="fm-bottom-glow-core" />
      </div>

      {/* ── Data block column going down ──────────────── */}
      <div className="fm-data-column">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="fm-dcol-block" style={{ animationDelay: `${i * 0.25}s` }}>
            <div className="fm-dcol-cube fm-dcol-cube-l" />
            <div className="fm-dcol-cube fm-dcol-cube-r" />
          </div>
        ))}
      </div>

      {/* ── Ground grid ───────────────────────────────── */}
      <div className="fm-ground">
        <div className="fm-ggrid" />
        <div className="fm-gspot" />
      </div>

      {/* ── Side circular icons ───────────────────────── */}
      <div className="fm-side-icon fm-si-1">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />
        </svg>
      </div>
      <div className="fm-side-icon fm-si-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="2" y="3" width="20" height="6" rx="1" />
          <circle cx="17" cy="6" r="1" fill="currentColor" />
          <circle cx="14" cy="6" r="1" fill="currentColor" />
          <rect x="2" y="15" width="20" height="6" rx="1" />
          <circle cx="17" cy="18" r="1" fill="currentColor" />
          <circle cx="14" cy="18" r="1" fill="currentColor" />
        </svg>
      </div>
    </div>
  );
}

/* ── Global Cube Config (Diagonal downward paths) ──────── */
interface GlobalCube {
  anim: string;
  delay: string;
  dur: string;
  cls: string;
}

const GLOBAL_CUBES: GlobalCube[] = [
  // Left Column (gray-light) -> Tapers center-left
  { anim: 'fm-descend-l', delay: '0s', dur: '3.2s', cls: 'fm-cube-light' },
  { anim: 'fm-descend-l', delay: '0.8s', dur: '3.4s', cls: 'fm-cube-dark' },
  { anim: 'fm-descend-l', delay: '1.6s', dur: '3.0s', cls: 'fm-cube-light' },
  { anim: 'fm-descend-l', delay: '2.4s', dur: '3.3s', cls: 'fm-cube-dark' },

  // Center Column (mixed) -> Stays center
  { anim: 'fm-descend-c', delay: '0.3s', dur: '3.1s', cls: 'fm-cube-dark' },
  { anim: 'fm-descend-c', delay: '1.1s', dur: '2.9s', cls: 'fm-cube-light' },
  { anim: 'fm-descend-c', delay: '1.9s', dur: '3.5s', cls: 'fm-cube-purple' },
  { anim: 'fm-descend-c', delay: '2.7s', dur: '3.2s', cls: 'fm-cube-light' },

  // Right Column (purple) -> Tapers center-right
  { anim: 'fm-descend-r', delay: '0.6s', dur: '2.9s', cls: 'fm-cube-purple' },
  { anim: 'fm-descend-r', delay: '1.4s', dur: '3.6s', cls: 'fm-cube-dark' },
  { anim: 'fm-descend-r', delay: '2.2s', dur: '3.2s', cls: 'fm-cube-purple' },
  { anim: 'fm-descend-r', delay: '3.0s', dur: '3.4s', cls: 'fm-cube-dark' },
];

/* ── CSS ──────────────────────────────────────────────── */
const FM_CSS = `
.fm-root {
  position: relative;
  width: 420px;
  height: 620px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 40px;
}

/* Background graphics */
.fm-bg-circle {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -55%);
  width: 380px; height: 380px;
  border-radius: 50%;
  border: 1px solid rgba(100, 90, 140, 0.12);
  background: radial-gradient(circle, rgba(60, 50, 90, 0.08) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}
.fm-bg-lines {
  position: absolute; inset: 0;
  pointer-events: none; z-index: 0;
}
.fm-bg-line {
  position: absolute; top: 0; bottom: 20%; width: 1px;
  background: linear-gradient(180deg, rgba(100, 90, 140, 0.08), rgba(100, 90, 140, 0.04), transparent);
}
.fm-bg-line-l { left: 18%; }
.fm-bg-line-r { right: 18%; }

/* ── Layer Layout ────────────────────────────────────── */
.fm-layer {
  position: relative;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: visible;
}
.fm-layer-back-only {
  position: absolute;
  width: 100%;
  pointer-events: none;
}

/* Cylinder Back Wall (Simulates 3D Inner Tube) */
.fm-cylinder-back {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(180deg, #0d0a1b 0%, #1c1630 100%);
  border: 1px solid rgba(130, 110, 200, 0.3);
  box-shadow:
    inset 0 4px 12px rgba(0, 0, 0, 0.95),
    inset 0 -2px 8px rgba(255, 255, 255, 0.05);
  z-index: 1;
}

/* Cylinder Front Wall */
.fm-cylinder-front {
  width: 100%;
  position: relative;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Hollow Top Rim */
.fm-top-rim {
  width: 100%;
  border-radius: 50%;
  background: transparent;
  border-style: solid;
  border-color: rgba(75, 65, 110, 0.85);
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.6),
    inset 0 2px 4px rgba(255, 255, 255, 0.1);
  box-sizing: border-box;
  position: relative;
  z-index: 4;
}

/* Cylinder Body Wall */
.fm-front-body {
  width: 100%;
  background: linear-gradient(180deg,
    rgba(50, 42, 78, 0.95) 0%,
    rgba(38, 32, 62, 0.98) 40%,
    rgba(28, 24, 48, 1) 100%);
  border-left: 1px solid rgba(100, 85, 150, 0.25);
  border-right: 1px solid rgba(100, 85, 150, 0.25);
  position: relative;
  z-index: 3;
  /* Clip top/bottom along ellipses while keeping sides 100% straight */
  clip-path: url(#fm-cyl-clip);
  -webkit-clip-path: url(#fm-cyl-clip);
  overflow: hidden;
}
.fm-front-body::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(90deg,
    rgba(0, 0, 0, 0.4) 0%,
    rgba(0, 0, 0, 0.08) 15%,
    transparent 40%,
    transparent 60%,
    rgba(0, 0, 0, 0.08) 85%,
    rgba(0, 0, 0, 0.4) 100%);
  pointer-events: none;
}
.fm-front-body::after {
  content: '';
  position: absolute; inset: 0;
  box-shadow:
    inset 4px 0 16px rgba(0, 0, 0, 0.4),
    inset -4px 0 16px rgba(0, 0, 0, 0.4);
  pointer-events: none;
}

/* Hollow Bottom Rim */
.fm-bottom-rim {
  width: 100%;
  border-radius: 50%;
  background: transparent;
  border-style: solid;
  border-color: rgba(55, 48, 85, 0.9);
  box-shadow:
    inset 0 -2px 6px rgba(0, 0, 0, 0.6),
    0 2px 8px rgba(0, 0, 0, 0.5);
  box-sizing: border-box;
  position: relative;
  z-index: 4;
}

/* ── Proportional Layer Dimensions ──────────────────── */
/* Layer 1 */
.fm-layer-1 { width: 360px; }
.fm-layer-1.fm-layer-back-only { top: 40px; height: 93px; }
.fm-layer-1 .fm-cylinder-back { height: 28px; top: 8px; width: 344px; left: 8px; }
.fm-layer-1 .fm-top-rim       { height: 44px; border-width: 8px; margin-bottom: -22px; }
.fm-layer-1 .fm-front-body    { height: 55px; }
.fm-layer-1 .fm-bottom-rim    { height: 32px; border-width: 8px; margin-top: -16px; }

/* Layer 2 */
.fm-layer-2 { width: 290px; margin-top: 24px; }
.fm-layer-2.fm-layer-back-only { top: 157px; height: 76px; }
.fm-layer-2 .fm-cylinder-back { height: 24px; top: 7px; width: 276px; left: 7px; }
.fm-layer-2 .fm-top-rim       { height: 38px; border-width: 7px; margin-bottom: -19px; }
.fm-layer-2 .fm-front-body    { height: 46px; }
.fm-layer-2 .fm-bottom-rim    { height: 28px; border-width: 7px; margin-top: -14px; }

/* Layer 3 */
.fm-layer-3 { width: 220px; margin-top: 24px; }
.fm-layer-3.fm-layer-back-only { top: 257px; height: 62px; }
.fm-layer-3 .fm-cylinder-back { height: 20px; top: 6px; width: 208px; left: 6px; }
.fm-layer-3 .fm-top-rim       { height: 32px; border-width: 6px; margin-bottom: -16px; }
.fm-layer-3 .fm-front-body    { height: 38px; }
.fm-layer-3 .fm-bottom-rim    { height: 24px; border-width: 6px; margin-top: -12px; }

/* Layer 4 */
.fm-layer-4 { width: 155px; margin-top: 24px; }
.fm-layer-4.fm-layer-back-only { top: 343px; height: 48px; }
.fm-layer-4 .fm-cylinder-back { height: 16px; top: 5px; width: 145px; left: 5px; }
.fm-layer-4 .fm-top-rim       { height: 26px; border-width: 5px; margin-bottom: -13px; }
.fm-layer-4 .fm-front-body    { height: 30px; }
.fm-layer-4 .fm-bottom-rim    { height: 20px; border-width: 5px; margin-top: -10px; }

/* ── Global Cubes Stream (Layered between Back/Front) ── */
.fm-global-cubes {
  position: absolute;
  top: 40px;
  width: 360px;
  height: 480px;
  z-index: 2;
  pointer-events: none;
}
.fm-cube {
  position: absolute;
  width: 12px; height: 12px;
  border-radius: 2px;
  animation-iteration-count: infinite;
  animation-timing-function: linear;
}
.fm-cube-light {
  background: linear-gradient(135deg, rgba(140, 130, 170, 0.8), rgba(95, 85, 130, 0.6));
  border: 1px solid rgba(160, 150, 195, 0.3);
}
.fm-cube-dark {
  background: linear-gradient(135deg, rgba(55, 48, 85, 0.9), rgba(35, 30, 60, 0.8));
  border: 1px solid rgba(80, 70, 120, 0.25);
}
.fm-cube-purple {
  background: linear-gradient(135deg, rgba(125, 80, 190, 0.85), rgba(75, 45, 135, 0.65));
  border: 1px solid rgba(145, 100, 205, 0.35);
}

/* Diagonal descent animations tapering inward */
@keyframes descendL {
  0% { top: -20px; left: 24%; opacity: 0; transform: scale(1.15) rotate(15deg); }
  10% { opacity: 0.85; }
  90% { opacity: 0.85; }
  100% { top: 460px; left: 45%; opacity: 0; transform: scale(0.7) rotate(15deg); }
}
@keyframes descendC {
  0% { top: -20px; left: 50%; opacity: 0; transform: scale(1.15) rotate(15deg); }
  10% { opacity: 0.85; }
  90% { opacity: 0.85; }
  100% { top: 460px; left: 50%; opacity: 0; transform: scale(0.7) rotate(15deg); }
}
@keyframes descendR {
  0% { top: -20px; left: 74%; opacity: 0; transform: scale(1.15) rotate(15deg); }
  10% { opacity: 0.85; }
  90% { opacity: 0.85; }
  100% { top: 460px; left: 53%; opacity: 0; transform: scale(0.7) rotate(15deg); }
}

.fm-descend-l { animation-name: descendL; }
.fm-descend-c { animation-name: descendC; }
.fm-descend-r { animation-name: descendR; }

/* ── Bottom glow ellipse ────────────────────────── */
.fm-bottom-glow {
  position: relative;
  width: 80px;
  margin-top: 20px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}
.fm-bottom-glow-ring {
  width: 100%;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(180deg,
    rgba(100, 60, 200, 0.45) 0%,
    rgba(70, 40, 160, 0.6) 50%,
    rgba(50, 30, 120, 0.3) 100%);
  border: 1px solid rgba(130, 90, 220, 0.4);
  box-shadow:
    0 0 20px rgba(100, 60, 200, 0.4),
    0 0 40px rgba(100, 60, 200, 0.2);
}
.fm-bottom-glow-core {
  width: 50%;
  height: 6px;
  margin-top: -3px;
  border-radius: 50%;
  background: rgba(160, 120, 255, 0.6);
  box-shadow: 0 0 16px rgba(160, 120, 255, 0.5);
}

/* ── Data block column ──────────────────────────── */
@keyframes dcolPulse {
  0%, 100% { opacity: 0.55; }
  50%      { opacity: 0.95; }
}
.fm-data-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  margin-top: 8px;
  z-index: 2;
  flex-shrink: 0;
}
.fm-dcol-block {
  display: flex;
  gap: 2px;
  animation: dcolPulse 2s ease-in-out infinite;
}
.fm-dcol-cube {
  width: 8px; height: 8px;
  border-radius: 1px;
}
.fm-dcol-cube-l {
  background: linear-gradient(135deg, rgba(140, 110, 200, 0.6), rgba(80, 60, 140, 0.5));
  border: 1px solid rgba(140, 110, 200, 0.25);
}
.fm-dcol-cube-r {
  background: linear-gradient(135deg, rgba(180, 100, 220, 0.5), rgba(120, 60, 180, 0.4));
  border: 1px solid rgba(180, 100, 220, 0.2);
}

/* ── Ground grid ────────────────────────────────── */
.fm-ground {
  position: relative;
  width: 130%;
  height: 50px;
  margin-top: 10px;
  z-index: 1;
  perspective: 250px;
  overflow: hidden;
  flex-shrink: 0;
}
.fm-ggrid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(120, 80, 180, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(120, 80, 180, 0.1) 1px, transparent 1px);
  background-size: 28px 18px;
  transform: rotateX(60deg);
  transform-origin: center top;
  mask-image: radial-gradient(ellipse 80% 100% at 50% 0%, black 10%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse 80% 100% at 50% 0%, black 10%, transparent 70%);
}
.fm-gspot {
  position: absolute; top: 0; left: 50%;
  transform: translateX(-50%);
  width: 80px; height: 30px;
  border-radius: 50%;
  background: radial-gradient(ellipse, rgba(120, 70, 200, 0.2), transparent 70%);
  filter: blur(6px);
}

/* ── Side circular icons ────────────────────────── */
.fm-side-icon {
  position: absolute;
  width: 42px; height: 42px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: rgba(140, 130, 175, 0.5);
  background: rgba(30, 26, 50, 0.4);
  border: 1px solid rgba(100, 90, 145, 0.15);
  z-index: 4;
  backdrop-filter: blur(4px);
}
.fm-si-1 { left: -8px; top: 38%; }
.fm-si-2 { right: -8px; top: 35%; }

/* ── Responsive scale transforms ────────────────── */
@media (max-width: 1100px) {
  .fm-root { transform: scale(0.88); transform-origin: center top; }
}
@media (max-width: 900px) {
  .fm-root { transform: scale(0.78); transform-origin: center top; }
  .fm-side-icon { display: none; }
}
@media (max-width: 639px) {
  .fm-root { transform: scale(0.65); transform-origin: center top; }
}
`;
