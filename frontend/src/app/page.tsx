import { Navbar } from '@/components/landing/Navbar';
import { Hero } from '@/components/landing/Hero';
import { TrustedBy } from '@/components/landing/TrustedBy';

export default function LandingPage() {
  return (
    <div className="min-h-screen w-full overflow-x-hidden" style={{ background: 'var(--bg-primary)' }}>
      <Navbar />
      <Hero />
      <TrustedBy />
    </div>
  );
}
