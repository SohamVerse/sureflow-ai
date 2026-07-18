'use client';
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { authApi } from '@/lib/api';

export interface User {
  email: string;
  role: 'cto' | 'plant_manager' | 'operator';
  plantId?: string | null;
  name: string;
}

interface AuthContextType {
  user: User | null;
  /** True until the stored session has been read from localStorage. Guards must
   *  wait for this, otherwise they act on a not-yet-restored (null) user. */
  loading: boolean;
  targetPlantId: string | null;
  setTargetPlantId: (plantId: string | null) => void;
  login: (email: string, pass: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

// Demo accounts for the login screen's quick-fill (credentials are verified by
// the backend, not here — these are just display hints).
export const DEMO_ACCOUNTS: Array<{ email: string; pass: string; label: string }> = [
  { email: 'cto@sureflow.ai', pass: 'Sureflow_CTO_2026!', label: 'CTO (Global)' },
  { email: 'karnataka@sureflow.ai', pass: 'Sureflow_Plant_2026!', label: 'Karnataka Manager (PLANT-001)' },
];

// Wipes every key that makes up a session. Used whenever the stored session is
// incomplete or rejected, so we never leave half of it behind.
function clearStoredSession() {
  localStorage.removeItem('sureflow_token');
  localStorage.removeItem('sureflow_user');
  localStorage.removeItem('sureflow_target_plant');
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [targetPlantId, setTargetPlantIdState] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const stored = localStorage.getItem('sureflow_user');
    const token = localStorage.getItem('sureflow_token');
    // A session is only valid when BOTH the user and the token are present.
    // A half-written session used to bounce the browser between /login and
    // /industrial forever, because each route's guard read a different key.
    if (stored && token) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        clearStoredSession();
      }
    } else if (stored || token) {
      clearStoredSession();
    }
    const storedTarget = localStorage.getItem('sureflow_target_plant');
    if (storedTarget) setTargetPlantIdState(storedTarget);
    setLoading(false);
  }, []);

  const setTargetPlantId = (plantId: string | null) => {
    setTargetPlantIdState(plantId);
    if (plantId) localStorage.setItem('sureflow_target_plant', plantId);
    else localStorage.removeItem('sureflow_target_plant');
  };

  const login = async (email: string, pass: string): Promise<boolean> => {
    try {
      const { access_token, user: u } = await authApi.login(email, pass);
      const mapped: User = {
        email: u.email,
        role: u.role as User['role'],
        plantId: u.plant_id,
        name: u.name,
      };
      localStorage.setItem('sureflow_token', access_token);
      localStorage.setItem('sureflow_user', JSON.stringify(mapped));
      setUser(mapped);
      return true;
    } catch {
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setTargetPlantIdState(null);
    clearStoredSession();
    router.replace('/login');
  };

  // Protect industrial routes. This reads the same `user` state that the login
  // page redirects on, so the two guards can never disagree and ping-pong.
  // `replace` keeps the bounce out of history, so Back still works.
  useEffect(() => {
    if (loading) return;
    if (pathname && pathname.startsWith('/industrial') && !user) {
      router.replace('/login');
    }
  }, [loading, user, pathname, router]);

  return (
    <AuthContext.Provider value={{ user, loading, targetPlantId, setTargetPlantId, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
