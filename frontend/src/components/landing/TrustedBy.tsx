'use client';
import { useEffect, useRef, useState } from 'react';
import { Fuel, Flame, Zap, Factory, Pill, Mountain } from 'lucide-react';

const INDUSTRIES = [
  { name: 'Petrochemical', icon: Fuel },
  { name: 'Oil & Gas', icon: Flame },
  { name: 'Power & Utilities', icon: Zap },
  { name: 'Manufacturing', icon: Factory },
  { name: 'Pharmaceuticals', icon: Pill },
  { name: 'Mining & Metals', icon: Mountain },
];

export function TrustedBy() {
  const DOUBLE_INDUSTRIES = [...INDUSTRIES, ...INDUSTRIES];
  const sectionRef = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      setIsVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(entry.target);
        }
      },
      {
        threshold: 0.1,
      }
    );

    const currentRef = sectionRef.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, []);

  return (
    <section
      ref={sectionRef}
      className={`px-4 sm:px-6 lg:px-8 pt-10 sm:pt-14 pb-16 sm:pb-24 border-t overflow-hidden ${
        isVisible ? 'entry-visible' : ''
      }`}
      style={{ borderColor: 'var(--border)' }}
    >
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes marquee {
            0% { transform: translateX(0); }
            100% { transform: translateX(-50%); }
          }
          .animate-marquee {
            animation: marquee 25s linear infinite;
          }
          .animate-marquee:hover {
            animation-play-state: paused;
          }
          
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
          
          .entry-animate-1,
          .entry-animate-2,
          .entry-animate-3 {
            opacity: 0;
            will-change: transform, opacity;
          }
          
          .entry-visible .entry-animate-1 {
            animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            animation-delay: 0.1s;
          }
          .entry-visible .entry-animate-2 {
            animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            animation-delay: 0.25s;
          }
          .entry-visible .entry-animate-3 {
            animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            animation-delay: 0.4s;
          }
        `
      }} />

      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-xl sm:text-2xl font-bold entry-animate-1" style={{ color: 'var(--text-primary)' }}>
          Built for the World&apos;s Most Demanding Plants
        </h2>
        <p className="mt-2 text-sm sm:text-base entry-animate-2" style={{ color: 'var(--text-secondary)' }}>
          Designed for the industries where downtime is measured in millions, not minutes.
        </p>
      </div>

      <div 
        className="relative w-full max-w-4xl mx-auto overflow-hidden mt-10 entry-animate-3"
        style={{
          maskImage: 'linear-gradient(to right, transparent, white 15%, white 85%, transparent)',
          WebkitMaskImage: 'linear-gradient(to right, transparent, white 15%, white 85%, transparent)',
        }}
      >
        <div className="flex animate-marquee whitespace-nowrap" style={{ width: 'max-content' }}>
          <div className="flex gap-16 pr-16 items-center">
            {DOUBLE_INDUSTRIES.map((item, index) => {
              const Icon = item.icon;
              return (
                <div
                  key={`list1-${index}`}
                  className="group flex items-center gap-3 text-sm sm:text-base font-semibold tracking-wide transition-colors duration-200 text-white/80 hover:text-white"
                  style={{ cursor: 'default' }}
                >
                  <Icon className="w-5 h-5 text-white/60 group-hover:text-white transition-colors duration-200" />
                  <span>{item.name}</span>
                </div>
              );
            })}
          </div>
          <div className="flex gap-16 pr-16 items-center">
            {DOUBLE_INDUSTRIES.map((item, index) => {
              const Icon = item.icon;
              return (
                <div
                  key={`list2-${index}`}
                  className="group flex items-center gap-3 text-sm sm:text-base font-semibold tracking-wide transition-colors duration-200 text-white/80 hover:text-white"
                  style={{ cursor: 'default' }}
                >
                  <Icon className="w-5 h-5 text-white/60 group-hover:text-white transition-colors duration-200" />
                  <span>{item.name}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

