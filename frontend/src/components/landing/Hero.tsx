import { FileText, Network, MessageSquare, Wrench, Lightbulb, ClipboardCheck, Zap } from 'lucide-react';

// Mirrors the six "Brain" colors already established in Sidebar.tsx (BRAIN_COLORS),
// so the landing page previews the same agent identity users see inside the app.
const LEFT_NODES = [
  { icon: FileText, color: '#3b82f6' },      // DOC_INTELLIGENCE
  { icon: Network, color: '#a855f7' },       // KG_AGENT
  { icon: MessageSquare, color: '#14b8a6' }, // SEARCH_AGENT
];
const RIGHT_NODES = [
  { icon: Wrench, color: '#f97316' },        // MAINTENANCE
  { icon: Lightbulb, color: '#eab308' },     // LESSONS_LEARNED
  { icon: ClipboardCheck, color: '#06b6d4' },// COMPLIANCE
];
const ALL_NODES = [...LEFT_NODES, ...RIGHT_NODES];

export function Hero() {
  return (
    <section className="relative px-4 sm:px-6 lg:px-8 pt-4 sm:pt-8 pb-0 overflow-hidden">
      {/* Ambient corner glows */}
      <div
        className="pointer-events-none absolute -top-24 -left-24 w-80 h-80 rounded-full blur-3xl opacity-25"
        style={{ background: 'var(--accent)' }}
      />
      <div
        className="pointer-events-none absolute -top-24 -right-24 w-80 h-80 rounded-full blur-3xl opacity-25"
        style={{ background: 'var(--accent-2)' }}
      />

      {/* Gradient border wrapper — the bright violet→pink outline is the hero's
          defining frame, matching the reference. The 1.5px padding reveals the
          gradient as a border around the near-black inner panel. */}
      <div
        className="relative max-w-4xl mx-auto rounded-[28px] p-[1.5px] animate-fade-in-up"
        style={{
          background: 'linear-gradient(145deg, #6366f1 0%, #a855f7 38%, #ec4899 55%, #6366f1 100%)',
          boxShadow: '0 0 80px rgba(139,92,246,0.18)',
        }}
      >
        <div
          className="rounded-[27px] px-6 sm:px-10 md:px-14 pt-12 sm:pt-14 pb-9 sm:pb-12 text-center"
          style={{
            background: 'rgba(8,12,20,0.92)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
          }}
        >
          <h1
            className="text-4xl sm:text-5xl md:text-[56px] font-extrabold tracking-tight leading-[1.05]"
            style={{ color: 'var(--text-primary)' }}
          >
            Downtime Down,<br className="hidden sm:block" />{' '}
            <span
              style={{
                background: 'linear-gradient(100deg, #f97316 0%, #ec4899 45%, #a855f7 100%)',
                WebkitBackgroundClip: 'text',
                backgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Uptime
            </span>{' '}
            Up
          </h1>

          {/* Hub-and-spoke diagram — bottom padding reserves a clean band for
              the connector traces so they don't collide with the description. */}
          <div className="relative mt-10 sm:mt-14 pb-4 sm:pb-20">
            <svg
              className="hidden sm:block absolute inset-x-0 w-full"
              style={{ top: '48px', height: '76px' }}
              viewBox="0 0 100 26"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              {LEFT_NODES.map((n, i) => {
                const x = 12 + i * 12.5;
                return (
                  <path
                    key={`l-${n.color}`}
                    d={`M${x},1 L${x},9 Q${x},15 ${x + 6},15 L45,15`}
                    fill="none"
                    stroke={n.color}
                    strokeWidth={0.7}
                    strokeLinecap="round"
                    opacity={0.6}
                  />
                );
              })}
              {RIGHT_NODES.map((n, i) => {
                const x = 88 - i * 12.5;
                return (
                  <path
                    key={`r-${n.color}`}
                    d={`M${x},1 L${x},9 Q${x},15 ${x - 6},15 L55,15`}
                    fill="none"
                    stroke={n.color}
                    strokeWidth={0.7}
                    strokeLinecap="round"
                    opacity={0.6}
                  />
                );
              })}
            </svg>

            <div className="relative flex flex-wrap items-center justify-center gap-3.5 sm:gap-5 md:gap-7">
              {LEFT_NODES.map(({ icon: Icon, color }) => (
                <div
                  key={color}
                  className="w-11 h-11 rounded-xl flex items-center justify-center"
                  style={{ border: `1.5px solid ${color}55`, background: `${color}14` }}
                >
                  <Icon size={18} style={{ color }} />
                </div>
              ))}

              <div className="flex items-center gap-2 mx-1 sm:mx-2">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: 'linear-gradient(135deg, #6366f1, #06b6d4)' }}
                >
                  <Zap size={16} color="white" />
                </div>
                <span className="font-bold text-base sm:text-lg" style={{ color: 'var(--text-primary)' }}>
                  SureFlow
                </span>
              </div>

              {RIGHT_NODES.map(({ icon: Icon, color }) => (
                <div
                  key={color}
                  className="w-11 h-11 rounded-xl flex items-center justify-center"
                  style={{ border: `1.5px solid ${color}55`, background: `${color}14` }}
                >
                  <Icon size={18} style={{ color }} />
                </div>
              ))}
            </div>
          </div>

          <p
            className="mt-7 text-base sm:text-lg max-w-md mx-auto"
            style={{ color: 'var(--text-secondary)' }}
          >
            SureFlow OS is a better way for your team to run industrial operations.
          </p>
        </div>
      </div>

      {/* Colored beams fading below the panel */}
      <div className="relative max-w-2xl mx-auto flex items-stretch justify-between h-20 sm:h-24 px-6 sm:px-12">
        {ALL_NODES.map(({ color }, i) => (
          <div
            key={i}
            className="w-[2.5px] rounded-full"
            style={{ background: `linear-gradient(to bottom, ${color}80, transparent)` }}
          />
        ))}
      </div>
    </section>
  );
}
