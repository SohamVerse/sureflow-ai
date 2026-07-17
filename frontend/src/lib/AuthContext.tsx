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
  targetPlantId: string | null;
  setTargetPlantId: (plantId: string | null) => void;
  login: (email: string, pass: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

// Demo accounts for the login screen's quick-fill (credentials are verified by
// the backend, not here — these are just display hints).
export const DEMO_ACCOUNTS: Array<{ email: string; pass: string; label: string }> = [
  { email: 'cto@sureflow.ai', pass: 'admin123', label: 'CTO (Global)' },
  { email: 'karnataka@sureflow.ai', pass: 'plant123', label: 'Karnataka Manager (PLANT-001)' },
];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [targetPlantId, setTargetPlantIdState] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const stored = localStorage.getItem('sureflow_user');
    if (stored) setUser(JSON.parse(stored));
    const storedTarget = localStorage.getItem('sureflow_target_plant');
    if (storedTarget) setTargetPlantIdState(storedTarget);
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
    setTargetPlantId(null);
    localStorage.removeItem('sureflow_token');
    localStorage.removeItem('sureflow_user');
    localStorage.removeItem('sureflow_target_plant');
    router.push('/login');
  };

  // Protect industrial routes — no token means redirect to login.
  useEffect(() => {
    if (pathname && pathname.startsWith('/industrial') && !localStorage.getItem('sureflow_token')) {
      router.push('/login');
    }
  }, [pathname, router]);

  return (
    <AuthContext.Provider value={{ user, targetPlantId, setTargetPlantId, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
