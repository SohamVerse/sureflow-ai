'use client';
import { useState } from 'react';
import type { PlantHierarchyNode } from '@/types';
import { ChevronRight, ChevronDown, Factory, MapPin, Cpu } from 'lucide-react';
import Link from 'next/link';

interface PlantHierarchyTreeProps {
  nodes: PlantHierarchyNode[];
}

const TYPE_ICONS: Record<string, typeof Factory> = {
  plant: Factory,
  area: MapPin,
  equipment: Cpu,
};

const TYPE_COLORS: Record<string, string> = {
  plant: '#6366f1',
  area: '#06b6d4',
  equipment: '#22c55e',
};

function TreeNode({ node, depth = 0 }: { node: PlantHierarchyNode; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const Icon = TYPE_ICONS[node.type] || Factory;
  const color = TYPE_COLORS[node.type] || '#6366f1';
  const hasChildren = node.children && node.children.length > 0;

  const content = (
    <div
      className="hierarchy-tree-node"
      onClick={() => hasChildren && setExpanded(!expanded)}
      style={{ paddingLeft: `${depth * 4}px` }}
    >
      {hasChildren ? (
        expanded ? <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} /> : <ChevronRight size={14} style={{ color: 'var(--text-muted)' }} />
      ) : (
        <div style={{ width: 14 }} />
      )}
      <div
        className="w-5 h-5 rounded flex items-center justify-center"
        style={{ background: `${color}20` }}
      >
        <Icon size={12} style={{ color }} />
      </div>
      <span style={{ color: 'var(--text-primary)' }}>{node.name}</span>
      {node.tag && (
        <span className="text-[10px] font-mono" style={{ color: 'var(--text-muted)' }}>
          {node.tag}
        </span>
      )}
      {node.equipment_count !== undefined && (
        <span className="text-[10px] ml-auto" style={{ color: 'var(--text-muted)' }}>
          {node.equipment_count} equip.
        </span>
      )}
      {node.status && (
        <span className={`badge badge-${node.status} ml-auto`} style={{ fontSize: '9px' }}>
          {node.status}
        </span>
      )}
    </div>
  );

  return (
    <div>
      {node.type === 'equipment' && node.tag ? (
        <Link href={`/industrial/equipment/${encodeURIComponent(node.tag)}`}>
          {content}
        </Link>
      ) : (
        content
      )}
      {hasChildren && expanded && (
        <div className="hierarchy-tree-children">
          {node.children!.map((child, i) => (
            <TreeNode key={child.id || i} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function PlantHierarchyTree({ nodes }: PlantHierarchyTreeProps) {
  if (nodes.length === 0) {
    return (
      <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
        <Factory size={32} className="mx-auto mb-2 opacity-30" />
        <p className="text-sm">No hierarchy data available.</p>
      </div>
    );
  }

  return (
    <div className="hierarchy-tree">
      {nodes.map((node, i) => (
        <TreeNode key={node.id || i} node={node} />
      ))}
    </div>
  );
}
