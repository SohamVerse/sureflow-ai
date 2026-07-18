'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Zap, Factory, MessageSquare, Wrench, ClipboardCheck, Upload, Cpu, Lightbulb, LogOut,
  Globe, BarChart3, Building2, Bell, ClipboardList, TrendingUp, Gauge, Search,
} from 'lucide-react';
import { useAuth } from '@/lib/AuthContext';
import { authApi, alertsApi } from '@/lib/api';
import { useSureflowStore } from '@/lib/store';
import { useEffect, useState } from 'react';

const INDUSTRIAL_NAV = [
  { href: '/industrial',            label: 'Plant Overview',     icon: Factory },
  { href: '/industrial/alerts',     label: 'Alerts',             icon: Bell },
  { href: '/industrial/copilot',    label: 'Industrial Copilot', icon: MessageSquare },
  { href: '/industrial/equipment',  label: 'Equipment',          icon: Cpu },
  { href: '/industrial/maintenance',label: 'Maintenance',        icon: Wrench },
  { href: '/industrial/work-orders', label: 'Work Orders',       icon: ClipboardList },
  { href: '/industrial/compliance', label: 'Compliance',         icon: ClipboardCheck },
  { href: '/industrial/lessons-learned', label: 'Lessons Learned', icon: Lightbulb },
  { href: '/industrial/trends',     label: 'Trends',             icon: TrendingUp },
  { href: '/industrial/ai-quality', label: 'AI Quality',         icon: Gauge },
  { href: '/industrial/upload',     label: 'Doc Upload',         icon: Upload },
];

const HQ_NAV = [
  { href: '/industrial/hq',           label: 'HQ Overview',    icon: Globe },
  { href: '/industrial/hq/compare',   label: 'Compare Plants', icon: BarChart3 },
  { href: '/industrial/hq/locations', label: 'Locations',      icon: Building2 },
];

const BRAIN_COLORS: Record<string, string> = {
  DOC_INTELLIGENCE: '#3b82f6',
  KG_AGENT: '#a855f7',
  SEARCH_AGENT: '#14b8a6',
  MAINTENANCE: '#f97316',
  LESSONS_LEARNED: '#eab308',
  COMPLIANCE: '#06b6d4',
};

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { agents, fetchAgents } = useSureflowStore();
  const { logout, user, targetPlantId, setTargetPlantId } = useAuth();
  const [plants, setPlants] = useState<Array<{ plant_id: string; name: string }>>([]);
  const [alertCount, setAlertCount] = useState(0);
  const [searchQ, setSearchQ] = useState('');

  const submitSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQ.trim()) router.push(`/industrial/search?q=${encodeURIComponent(searchQ.trim())}`);
  };

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(() => {
      fetchAgents();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchAgents]);

  // Load accessible plants for the CTO switcher (reflects real/created plants).
  useEffect(() => {
    if (user?.role === 'cto') {
      authApi.me().then(d => setPlants(d.plants)).catch(() => {});
    }
  }, [user]);

  // Poll the open-alert count for the sidebar bell badge.
  useEffect(() => {
    if (!user) return;
    const load = () => alertsApi.count().then(d => setAlertCount(d.count)).catch(() => {});
    load();
    const iv = setInterval(load, 15000);
    return () => clearInterval(iv);
  }, [user, targetPlantId]);

  const onSwitchPlant = (value: string) => {
    setTargetPlantId(value || null);
    // Reload so every dashboard re-fetches scoped to the newly selected plant.
    if (typeof window !== 'undefined') window.location.reload();
  };

  const workingCount = agents.filter(a => a.status === 'working').length;

  const renderNavItem = ({ href, label, icon: Icon }: { href: string; label: string; icon: typeof Factory }) => {
    const isActive = (href === '/industrial' || href === '/industrial/hq')
      ? pathname === href
      : pathname.startsWith(href);
    return (
      <Link
        key={href}
        href={href}
        className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150"
        style={{
          color: isActive ? 'white' : 'var(--text-secondary)',
          background: isActive
            ? 'linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(168, 85, 247, 0.05))'
            : 'transparent',
          borderLeft: isActive ? '2px solid #a855f7' : '2px solid transparent',
        }}
      >
        <Icon size={16} style={{ color: isActive ? '#a855f7' : 'var(--text-muted)' }} />
        <span className="flex-1">{label}</span>
        {href === '/industrial/alerts' && alertCount > 0 && (
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full" style={{ background: '#ef4444', color: 'white', minWidth: '18px', textAlign: 'center' }}>
            {alertCount}
          </span>
        )}
      </Link>
    );
  };

  return (
    <aside
      className="flex flex-col w-64 h-screen border-r overflow-y-auto"
      style={{
        background: 'var(--bg-secondary)',
        borderColor: 'var(--border)',
        flexShrink: 0,
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b" style={{ borderColor: 'var(--border)' }}>
        <div
          className="flex items-center justify-center w-9 h-9 rounded-xl"
          style={{ background: 'linear-gradient(135deg, #a855f7, #6d28d9)' }}
        >
          <Zap size={18} color="white" />
        </div>
        <div>
          <div className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>SureFlow</div>
          <div className="text-xs flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
            Industrial Intelligence
          </div>
        </div>
      </div>

      {/* Location Selector (CTO Only) */}
      {user && user.role === 'cto' && (
        <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="text-[10px] font-semibold mb-2 uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
            Location Access
          </div>
          <select
            value={targetPlantId || ''}
            onChange={(e) => onSwitchPlant(e.target.value)}
            className="w-full bg-[#1a1a1a] border border-[#333] text-xs rounded-lg p-2 text-white outline-none focus:border-[#6366f1]"
          >
            <option value="">Global (All Plants)</option>
            {plants.map(p => (
              <option key={p.plant_id} value={p.plant_id}>{p.name} ({p.plant_id})</option>
            ))}
          </select>
        </div>
      )}

      {/* Global search */}
      <form onSubmit={submitSearch} className="px-4 pt-4">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--text-muted)' }} />
          <input
            value={searchQ}
            onChange={e => setSearchQ(e.target.value)}
            placeholder="Search everything…"
            className="w-full pl-9 pr-3 py-2 rounded-xl text-sm outline-none"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
          />
        </div>
      </form>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {user?.role === 'cto' && (
          <>
            <div className="nav-section-label">Headquarters</div>
            {HQ_NAV.map(renderNavItem)}
          </>
        )}
        <div className="nav-section-label">Industrial Intelligence</div>
        {INDUSTRIAL_NAV.map(renderNavItem)}
      </nav>

      {/* Brain Status Panel */}
      <div className="px-4 py-4 border-t" style={{ borderColor: 'var(--border)' }}>
        <div className="text-xs font-semibold mb-3 uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
          Brain Status
        </div>
        <div className="space-y-1.5">
          {agents.length === 0 ? (
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Backend offline</div>
          ) : (
            agents.slice(0, 10).map(agent => (
              <div key={agent.id} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2 h-2 rounded-full transition-all duration-300"
                    style={{
                      background: BRAIN_COLORS[agent.id] || '#6366f1',
                      opacity: agent.status === 'working' ? 1 : 0.3,
                      boxShadow: agent.status === 'working' ? `0 0 6px ${BRAIN_COLORS[agent.id] || '#6366f1'}` : 'none',
                    }}
                  />
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                    {agent.id}
                  </span>
                </div>
                <span className="text-xs" style={{ color: agent.status === 'working' ? '#10b981' : 'var(--text-muted)', fontSize: '10px' }}>
                  {agent.status}
                </span>
              </div>
            ))
          )}
        </div>
        {workingCount > 0 && (
          <div className="mt-3 flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: 'rgba(99,102,241,0.1)' }}>
            <div className="status-dot-working" />
            <span className="text-xs font-medium" style={{ color: '#818cf8' }}>
              {workingCount} brain{workingCount > 1 ? 's' : ''} active
            </span>
          </div>
        )}
      </div>

      {/* User Profile / Logout */}
      {user && (
        <div className="p-4 border-t" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>{user.name}</span>
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{user.role}</span>
            </div>
            <button 
              onClick={logout}
              className="p-2 rounded-lg hover:bg-white/5 transition-colors"
              title="Logout"
            >
              <LogOut size={16} style={{ color: 'var(--text-secondary)' }} />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
