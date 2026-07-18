'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth, DEMO_ACCOUNTS } from '@/lib/AuthContext';

export default function LoginPage() {
  const { login, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) {
      router.push('/industrial');
    }
  }, [user, router]);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const ok = await login(email, password);
    setLoading(false);
    if (ok) {
      window.location.href = '/industrial';
    } else {
      setError('Invalid email or password');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#04060c] relative overflow-hidden">
      {/* Ambient background glow */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '600px',
        height: '600px',
        background: 'radial-gradient(circle, rgba(140, 80, 220, 0.15) 0%, transparent 60%)',
        pointerEvents: 'none',
        zIndex: 0,
      }} />

      <div 
        className="w-full max-w-md p-8 rounded-2xl z-10 relative"
        style={{
          background: 'rgba(10, 14, 24, 0.6)',
          border: '1px solid #3f1495',
          boxShadow: '0 50px 100px -20px rgba(0, 0, 0, 0.85), 0 40px 120px rgba(140, 80, 220, 0.15), inset 0 1px 0 rgba(255,255,255,0.02)',
          backdropFilter: 'blur(20px)',
        }}
      >
        <h1 className="text-3xl font-bold mb-2 text-white">
          <span style={{ color: '#a855f7' }}>Welcome</span> Back
        </h1>
        <p className="text-gray-400 mb-8">Sign in to your Sureflow account.</p>
        
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-500 text-sm shadow-[0_0_15px_rgba(239,68,68,0.15)]">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-[#0a0e18]/80 border border-[#3f1495]/40 rounded-xl text-white focus:outline-none focus:border-[#a855f7] transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.4)]"
              placeholder="cto@sureflow.ai"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-[#0a0e18]/80 border border-[#3f1495]/40 rounded-xl text-white focus:outline-none focus:border-[#a855f7] transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.4)]"
              placeholder="••••••••"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 hover:opacity-90 disabled:opacity-60 text-black font-semibold rounded-full transition-all mt-4"
            style={{
              background: 'white',
              boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 4px 14px rgba(255,255,255,0.15)'
            }}
          >
            {loading ? 'Signing in…' : 'Start Now'}
          </button>
        </form>

        <div className="mt-10 pt-8 border-t border-[#3f1495]/30">
          <h3 className="text-sm font-semibold text-[#a855f7] mb-4">Demo Accounts:</h3>
          <div className="space-y-3">
            {DEMO_ACCOUNTS.map((acct) => (
              <div 
                key={acct.email} 
                className="p-3 rounded-lg text-sm cursor-pointer transition-all border border-transparent hover:border-[#3f1495]/60 hover:bg-[#3f1495]/10"
                style={{ background: 'rgba(255,255,255,0.02)' }}
                onClick={() => { setEmail(acct.email); setPassword(acct.pass); }}
              >
                <div className="font-medium text-white">{acct.label}</div>
                <div className="text-gray-400 font-mono text-xs mt-1">
                  {acct.email} / {acct.pass}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
