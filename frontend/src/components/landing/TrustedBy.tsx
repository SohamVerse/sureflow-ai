const INDUSTRIES = [
  'Petrochemical',
  'Oil & Gas',
  'Power & Utilities',
  'Manufacturing',
  'Pharmaceuticals',
  'Mining & Metals',
];

export function TrustedBy() {
  return (
    <section
      className="px-4 sm:px-6 lg:px-8 pt-10 sm:pt-14 pb-16 sm:pb-24 border-t"
      style={{ borderColor: 'var(--border)' }}
    >
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-xl sm:text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
          Built for the World&apos;s Most Demanding Plants
        </h2>
        <p className="mt-2 text-sm sm:text-base" style={{ color: 'var(--text-secondary)' }}>
          Designed for the industries where downtime is measured in millions, not minutes.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-x-8 gap-y-4 sm:gap-x-12">
          {INDUSTRIES.map(name => (
            <span
              key={name}
              className="text-sm sm:text-base font-semibold tracking-wide"
              style={{ color: 'var(--text-muted)' }}
            >
              {name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
