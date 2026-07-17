'use client';
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export interface User {
  email: string;
  role: 'cto' | 'plant_manager';
  plantId?: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  targetPlantId: string | null;
  setTargetPlantId: (plantId: string | null) => void;
  login: (email: string, pass: string) => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const USERS: Record<string, { pass: string, user: User }> = {
  'cto@sureflow.ai': {
    pass: 'admin123',
    user: { email: 'cto@sureflow.ai', role: 'cto', name: 'CTO (Global)' }
  },
  'karnataka@sureflow.ai': {
    pass: 'plant123',
    user: { email: 'karnataka@sureflow.ai', role: 'plant_manager', plantId: 'PLANT-001', name: 'Karnataka Manager' }
  }
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [targetPlantId, setTargetPlantIdState] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const stored = localStorage.getItem('sureflow_user');
    if (stored) {
      setUser(JSON.parse(stored));
    }
    const storedTarget = localStorage.getItem('sureflow_target_plant');
    if (storedTarget) {
      setTargetPlantIdState(storedTarget);
    }
  }, []);

  const setTargetPlantId = (plantId: string | null) => {
    setTargetPlantIdState(plantId);
    if (plantId) {
      localStorage.setItem('sureflow_target_plant', plantId);
    } else {
      localStorage.removeItem('sureflow_target_plant');
    }
  };

  const login = (email: string, pass: string) => {
    const account = USERS[email];
    if (account && account.pass === pass) {
      setUser(account.user);
      localStorage.setItem('sureflow_user', JSON.stringify(account.user));
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
    setTargetPlantId(null);
    localStorage.removeItem('sureflow_user');
    localStorage.removeItem('sureflow_target_plant');
    router.push('/login');
  };

  // Protect industrial routes
  useEffect(() => {
    if (pathname && pathname.startsWith('/industrial') && !localStorage.getItem('sureflow_user')) {
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
