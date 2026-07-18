
const NAV_LINKS = ['Why SureFlow', 'Platform', 'Capabilities', 'Integrations', 'Resources', 'Company'];

export function Navbar() {
  return (
    <header className="w-full relative z-10">
      {/* Beveled top-center notch, echoing the reference's raised header tab. */}
      <div
        className="hidden md:block absolute top-0 left-1/2 -translate-x-1/2 h-9 w-[46%]"
        style={{
          background: 'var(--bg-secondary)',
          clipPath: 'polygon(6% 0, 94% 0, 100% 100%, 0 100%)',
          opacity: 0.7,
        }}
        aria-hidden="true"
      />
      <nav className="relative max-w-6xl mx-auto flex items-center justify-between px-4 sm:px-6 lg:px-8 py-5 sm:py-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9">
            <img src="/logo.png" alt="SureFlow" className="w-8 h-8 object-contain" />
          </div>
          <span className="font-bold text-lg" style={{ color: 'var(--text-primary)' }}>SureFlow</span>
        </div>

        <div className="hidden lg:flex items-center gap-8">
          {NAV_LINKS.map(label => (
            <span
              key={label}
              className="text-sm font-medium"
              style={{ color: 'var(--text-secondary)' }}
            >
              {label}
            </span>
          ))}
        </div>
      </nav>
    </header>
  );
}
