'use client';
import { useEffect, useState } from 'react';
import { useSureflowStore } from '@/lib/store';
import { systemApi } from '@/lib/api';
import { EquipmentCard } from '@/components/industrial/EquipmentCard';
import { Search, LayoutGrid, List, Cpu, Filter, Download } from 'lucide-react';

export default function EquipmentDashboard() {
  const { industrialEquipment, loadingIndustrial, fetchIndustrialEquipment } = useSureflowStore();
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterArea, setFilterArea] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    fetchIndustrialEquipment();
  }, [fetchIndustrialEquipment]);

  // Derive unique areas
  const areas = [...new Set(industrialEquipment.map(e => e.area))].sort();

  // Filter
  const filtered = industrialEquipment.filter(e => {
    const matchSearch = !search ||
      e.tag.toLowerCase().includes(search.toLowerCase()) ||
      e.name.toLowerCase().includes(search.toLowerCase()) ||
      e.type.toLowerCase().includes(search.toLowerCase());
    const matchArea = !filterArea || e.area === filterArea;
    const matchStatus = !filterStatus || e.status === filterStatus;
    return matchSearch && matchArea && matchStatus;
  });

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <Cpu size={28} className="inline mr-2" style={{ color: '#3b82f6' }} />
          Equipment<span className="gradient-text"> Dashboard</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Browse and monitor all plant equipment. Click any card for full details and live sensor data.
        </p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 mb-6 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        {/* Search */}
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
            <input
              id="equipment-search"
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search by tag, name, or type..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm outline-none"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
            />
          </div>
        </div>

        {/* Area Filter */}
        <div className="flex items-center gap-2">
          <Filter size={14} style={{ color: 'var(--text-muted)' }} />
          <select
            id="area-filter"
            value={filterArea}
            onChange={e => setFilterArea(e.target.value)}
            className="px-3 py-2.5 rounded-xl text-sm outline-none cursor-pointer"
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
            }}
          >
            <option value="">All Areas</option>
            {areas.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>

        {/* Status Filter */}
        <select
          id="status-filter"
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          className="px-3 py-2.5 rounded-xl text-sm outline-none cursor-pointer"
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid var(--border)',
            color: 'var(--text-primary)',
          }}
        >
          <option value="">All Status</option>
          <option value="operational">Operational</option>
          <option value="warning">Warning</option>
          <option value="critical">Critical</option>
          <option value="offline">Offline</option>
        </select>

        {/* View Toggle */}
        <div className="flex gap-1 p-1 rounded-lg" style={{ background: 'rgba(255,255,255,0.04)' }}>
          <button
            onClick={() => setViewMode('grid')}
            className="p-2 rounded-lg"
            style={{
              background: viewMode === 'grid' ? 'rgba(99,102,241,0.15)' : 'transparent',
              color: viewMode === 'grid' ? '#818cf8' : 'var(--text-muted)',
            }}
          >
            <LayoutGrid size={16} />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className="p-2 rounded-lg"
            style={{
              background: viewMode === 'list' ? 'rgba(99,102,241,0.15)' : 'transparent',
              color: viewMode === 'list' ? '#818cf8' : 'var(--text-muted)',
            }}
          >
            <List size={16} />
          </button>
        </div>

        {/* Export */}
        <button onClick={() => systemApi.exportCsv('equipment')} className="btn-ghost" style={{ padding: '9px 14px' }}>
          <Download size={15} /> CSV
        </button>
      </div>

      {/* Stats bar */}
      <div className="flex gap-4 mb-6 text-xs" style={{ color: 'var(--text-muted)' }}>
        <span>{filtered.length} equipment found</span>
        <span>·</span>
        <span>{filtered.filter(e => e.status === 'operational').length} operational</span>
        <span>·</span>
        <span className="text-yellow-500">{filtered.filter(e => e.status === 'warning').length} warning</span>
        <span>·</span>
        <span className="text-red-500">{filtered.filter(e => e.status === 'critical').length} critical</span>
      </div>

      {/* Equipment Grid/List */}
      {loadingIndustrial ? (
        <div className={`grid ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' : 'grid-cols-1'} gap-4`}>
          {[...Array(8)].map((_, i) => (
            <div key={i} className="skeleton h-36 rounded-2xl" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16" style={{ color: 'var(--text-muted)' }}>
          <Cpu size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg">No equipment found</p>
          <p className="text-sm mt-1">Try adjusting your filters or search term.</p>
        </div>
      ) : (
        <div className={`grid ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' : 'grid-cols-1'} gap-4`}>
          {filtered.map((eq, i) => (
            <EquipmentCard key={eq.tag} equipment={eq} delay={0.1 + i * 0.03} />
          ))}
        </div>
      )}
    </div>
  );
}
