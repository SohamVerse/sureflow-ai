'use client';

import { useState } from 'react';
import { useAuth, USERS } from '@/lib/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (login(email, password)) {
      window.location.href = '/industrial';
    } else {
      setError('Invalid email or password');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#050505]">
      <div className="w-full max-w-md p-8 bg-[#111] border border-[#222] rounded-2xl shadow-xl">
        <h1 className="text-3xl font-bold mb-2 text-white">Welcome Back</h1>
        <p className="text-gray-400 mb-8">Sign in to your Sureflow account.</p>
        
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-sm">
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
              className="w-full px-4 py-3 bg-[#1a1a1a] border border-[#333] rounded-xl text-white focus:outline-none focus:border-blue-500 transition-colors"
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
              className="w-full px-4 py-3 bg-[#1a1a1a] border border-[#333] rounded-xl text-white focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="••••••••"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors"
          >
            Sign In
          </button>
        </form>

        <div className="mt-8 pt-8 border-t border-[#222]">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">Demo Accounts:</h3>
          <div className="space-y-3">
            {Object.entries(USERS).map(([mail, data]) => (
              <div key={mail} className="p-3 bg-[#1a1a1a] rounded-lg text-sm cursor-pointer hover:bg-[#222] transition-colors" onClick={() => { setEmail(mail); setPassword(data.pass); }}>
                <div className="font-medium text-white">{data.user.name}</div>
                <div className="text-gray-400 font-mono text-xs mt-1">
                  {mail} / {data.pass}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
