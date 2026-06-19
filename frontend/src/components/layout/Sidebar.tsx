'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, FileText, Users, Network,
  BarChart3, Database, Zap, Brain, ShieldCheck,
} from 'lucide-react';
import { useSureflowStore } from '@/lib/store';
import { useEffect } from 'react';

const NAV_ITEMS = [
  { href: '/',          label: 'Command Center',   icon: LayoutDashboard },
  { href: '/brains',    label: 'Brain Roster',     icon: Brain,       badge: 'V2' },
  { href: '/content',   label: 'Content Pipeline', icon: FileText },
  { href: '/leads',     label: 'Lead Pipeline',    icon: Users },
  { href: '/agents',    label: 'Agent Console',    icon: Network },
  { href: '/approvals', label: 'Approval Center',  icon: ShieldCheck, highlight: true },
  { href: '/analytics', label: 'Analytics',        icon: BarChart3 },
  { href: '/vault',     label: 'Knowledge Vault',  icon: Database },
];

const BRAIN_COLORS: Record<string, string> = {
  CEO: '#6366f1', CMO: '#06b6d4', RESEARCH: '#f59e0b',
  SDR: '#10b981', AE: '#ec4899', RISK: '#ef4444',
  EMAIL: '#8b5cf6', ANALYST: '#fb923c',
};

export function Sidebar() {
  const pathname = usePathname();
  const { agents, fetchAgents, pendingApprovals, fetchPendingApprovals } = useSureflowStore();

  useEffect(() => {
    fetchAgents();
    if (fetchPendingApprovals) fetchPendingApprovals();
    const interval = setInterval(() => {
      fetchAgents();
      if (fetchPendingApprovals) fetchPendingApprovals();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchAgents, fetchPendingApprovals]);

  const workingCount = agents.filter(a => a.status === 'working').length;

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
          style={{ background: 'linear-gradient(135deg, #6366f1, #06b6d4)' }}
        >
          <Zap size={18} color="white" />
        </div>
        <div>
          <div className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>CompanyOS</div>
          <div className="text-xs flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
            Business Brain
            <span className="px-1 rounded text-[9px] font-bold" style={{ background: 'rgba(99,102,241,0.2)', color: '#818cf8' }}>V2</span>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon, badge, highlight }: any) => {
          const isActive = href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150"
              style={{
                color: isActive ? 'white' : 'var(--text-secondary)',
                background: isActive
                  ? 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(6,182,212,0.1))'
                  : 'transparent',
                borderLeft: isActive ? '2px solid #6366f1' : '2px solid transparent',
              }}
            >
              <Icon size={16} style={{ color: isActive ? '#818cf8' : highlight ? '#f59e0b' : 'var(--text-muted)' }} />
              <span className="flex-1">{label}</span>
              {badge && (
                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: 'rgba(99,102,241,0.2)', color: '#818cf8' }}>
                  {badge}
                </span>
              )}
              {href === '/approvals' && pendingApprovals > 0 && (
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full" style={{ background: '#f59e0b', color: '#000' }}>
                  {pendingApprovals}
                </span>
              )}
            </Link>
          );
        })}
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
            agents.slice(0, 6).map(agent => (
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
    </aside>
  );
}
