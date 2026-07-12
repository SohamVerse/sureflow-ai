import { Navbar } from '@/components/landing/Navbar';
import { HeroSection } from '@/components/landing/Hero';
import { TrustedBy } from '@/components/landing/TrustedBy';
import { DetailSection } from '@/components/landing/DetailSection';

export default function LandingPage() {
  return (
    <div className="min-h-screen w-full overflow-x-hidden" style={{ background: 'var(--bg-primary)' }}>
      {/* <Navbar /> */}
      <HeroSection />
      <TrustedBy />
      <DetailSection />
    </div>
  );
}
