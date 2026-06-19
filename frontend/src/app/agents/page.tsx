'use client';
import { useEffect, useCallback, useState } from 'react';
import ReactFlow, {
  Background, Controls, MiniMap, addEdge,
  useNodesState, useEdgesState, Handle, Position,
  type Connection, type Edge, type Node,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useSureflowStore } from '@/lib/store';
import { pipelineApi } from '@/lib/api';
import type { AgentNodeData, AgentType } from '@/types';
import { Play, Plus, Trash2, Cpu } from 'lucide-react';

const AGENT_COLORS: Record<AgentType, string> = {
  CEO:      '#6366f1',
  CMO:      '#06b6d4',
  RESEARCH: '#f59e0b',
  SDR:      '#10b981',
  AE:       '#ec4899',
  ANALYST:  '#8b5cf6',
  EMAIL:    '#8b5cf6',
  RISK:     '#ef4444',
};

const AGENT_MODELS: Record<AgentType, string> = {
  CEO:      'gemini-1.5-pro',
  CMO:      'gemini-1.5-pro',
  RESEARCH: 'gemini-1.5-pro',
  SDR:      'gemini-1.5-pro',
  AE:       'gemini-1.5-pro',
  ANALYST:  'gemini-1.5-pro',
  EMAIL:    'gemini-1.5-pro',
  RISK:     'gemini-1.5-pro',
};

// Custom Agent Node component for React Flow
function AgentNode({ data, selected }: { data: AgentNodeData; selected: boolean }) {
  const color = AGENT_COLORS[data.agent] || '#8b5cf6';
  
  const riskColor = data.risk_level === 'low' ? '#10b981' :
                    data.risk_level === 'medium' ? '#f59e0b' :
                    data.risk_level === 'high' ? '#ef4444' :
                    data.risk_level === 'critical' ? '#dc2626' : 'var(--text-muted)';

  return (
    <div className={`agent-node ${selected ? 'selected' : ''}`} style={{ borderColor: selected ? color : `${color}66` }}>
      <Handle type="target" position={Position.Top} className="w-2 h-2 opacity-0" />
      
      {/* V2: Confidence / Risk Overlay */}
      {(data.confidence != null || data.risk_level != null) && (
        <div className="absolute -top-3 -right-3 flex flex-col gap-1 z-10">
          {data.confidence != null && (
            <div className="flex items-center justify-center w-8 h-8 rounded-full shadow-lg text-[10px] font-bold" 
                 style={{ background: '#222', border: `2px solid ${color}`, color: '#fff' }}>
              {data.confidence}%
            </div>
          )}
          {data.risk_level != null && (
            <div className="flex items-center justify-center px-2 py-0.5 rounded shadow-lg text-[9px] font-bold uppercase" 
                 style={{ background: '#222', border: `1px solid ${riskColor}`, color: riskColor }}>
              {data.risk_level}
            </div>
          )}
        </div>
      )}

      <div className="flex items-center gap-2 mb-2">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: `${color}22` }}>
          <Cpu size={13} style={{ color }} />
        </div>
        <div>
          <div className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>{data.agent}</div>
          <div className="text-xs font-mono" style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
            {AGENT_MODELS[data.agent] || 'default-model'}
          </div>
        </div>
      </div>
      {data.status && (
        <div className="flex items-center gap-1.5 mt-2">
          <div className={data.status === 'running' ? 'status-dot-working' : 'status-dot-idle'} />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{data.status}</span>
        </div>
      )}
      {data.instruction && (
        <p className="text-xs mt-2 line-clamp-2" style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>
          {data.instruction}
        </p>
      )}
      <Handle type="source" position={Position.Bottom} className="w-2 h-2 opacity-0" />
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

// Default graph — the standard Sureflow pipeline
const DEFAULT_NODES: Node<AgentNodeData>[] = [
  { id: 'ceo',      type: 'agentNode', position: { x: 500, y: 50  }, data: { agent: 'CEO',      instruction: 'Analyze tech trends & orchestrate FinTech/LMS strategies', status: 'idle' } },
  { id: 'cmo',      type: 'agentNode', position: { x: 50,  y: 250 }, data: { agent: 'CMO',      instruction: 'Generate trend-based SaaS engagement content', status: 'idle' } },
  { id: 'research', type: 'agentNode', position: { x: 350, y: 250 }, data: { agent: 'RESEARCH', instruction: 'Analyze social media trends in FinTech & EdTech', status: 'idle' } },
  { id: 'sdr',      type: 'agentNode', position: { x: 650, y: 250 }, data: { agent: 'SDR',      instruction: 'Qualify leads for custom web/mobile app development', status: 'idle' } },
  { id: 'ae',       type: 'agentNode', position: { x: 650, y: 450 }, data: { agent: 'AE',       instruction: 'Draft SaaS proposal follow-ups', status: 'idle' } },
  { id: 'analyst',  type: 'agentNode', position: { x: 950, y: 250 }, data: { agent: 'ANALYST',  instruction: 'Track engagement and new revenue metrics', status: 'idle' } },
];

const DEFAULT_EDGES: Edge[] = [
  { id: 'ceo-cmo',      source: 'ceo', target: 'cmo',      animated: true, style: { strokeDasharray: '5, 5' }, type: 'smoothstep' },
  { id: 'ceo-research', source: 'ceo', target: 'research', animated: true, style: { strokeDasharray: '5, 5' }, type: 'smoothstep' },
  { id: 'ceo-sdr',      source: 'ceo', target: 'sdr',      animated: true, style: { strokeDasharray: '5, 5' }, type: 'smoothstep' },
  { id: 'ceo-analyst',  source: 'ceo', target: 'analyst',  animated: true, style: { strokeDasharray: '5, 5' }, type: 'smoothstep' },
  { id: 'sdr-ae',       source: 'sdr', target: 'ae',       animated: true, style: { strokeDasharray: '5, 5' }, type: 'smoothstep' },
];

const AGENT_TYPES: AgentType[] = ['CEO', 'CMO', 'RESEARCH', 'SDR', 'AE', 'ANALYST'];

export default function AgentConsole() {
  const { agents, fetchAgents, fetchPipelineItems, fetchKPIs, pipelineRunning } = useSureflowStore();
  const [nodes, setNodes, onNodesChange] = useNodesState(DEFAULT_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(DEFAULT_EDGES);
  const [selectedAgent, setSelectedAgent] = useState<AgentType>('CMO');
  const [instruction, setInstruction] = useState('');
  const [customGoal, setCustomGoal] = useState('');
  const [runResult, setRunResult] = useState<string | null>(null);

  useEffect(() => { fetchAgents(); }, [fetchAgents]);

  // Sync global agents status to React Flow nodes when main pipeline is running
  useEffect(() => {
    if (pipelineRunning) {
      setNodes(nds => nds.map(n => {
        const globalAgent = agents.find(a => a.id === n.data.agent);
        if (globalAgent && globalAgent.status !== n.data.status) {
          // Map 'working' -> 'running' for AgentNodeData
          const mappedStatus = globalAgent.status === 'working' ? 'running' : globalAgent.status;
          return { ...n, data: { ...n.data, status: mappedStatus as AgentNodeData['status'] } };
        }
        return n;
      }));
    }
  }, [agents, pipelineRunning, setNodes]);

  const onConnect = useCallback(
    (connection: Connection) => setEdges(eds => addEdge({ ...connection, type: 'smoothstep', animated: true, style: { strokeDasharray: '5, 5' } }, eds)),
    [setEdges]
  );

  const addAgentNode = () => {
    const newNode: Node<AgentNodeData> = {
      id: `${selectedAgent}-${Date.now()}`,
      type: 'agentNode',
      position: { x: Math.random() * 400 + 100, y: Math.random() * 200 + 100 },
      data: { agent: selectedAgent, instruction: instruction || 'Configure this agent...', status: 'idle' },
    };
    setNodes(nds => [...nds, newNode]);
    setInstruction('');
  };

  const deleteSelected = () => {
    setNodes(nds => nds.filter(n => !n.selected));
    setEdges(eds => eds.filter(e => !e.selected));
  };

  const runCustomGraph = async () => {
    const graphJson = JSON.stringify({
      nodes: nodes.map(n => ({ id: n.id, data: n.data, type: n.type })),
      edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target })),
    });

    setRunResult("Starting execution...");
    setNodes(nds => nds.map(n => ({ ...n, data: { ...n.data, status: 'idle' } })));

    try {
      const result = await pipelineApi.runCustom(graphJson, customGoal, undefined, (event) => {
        if (event.event === 'agent_update') {
          const nodeName = event.node.toUpperCase();
          const isRunning = event.update?.status === 'running';
          
          setNodes(nds => nds.map(n => {
            if (n.data.agent === nodeName) {
              return { ...n, data: { ...n.data, status: (isRunning ? 'running' : 'idle') as AgentNodeData['status'] } };
            }
            return n;
          }));
          
          if (!isRunning) {
            setRunResult(prev => `${prev}\n[${nodeName}] update received`);
          }
        } else if (event.event === 'complete') {
          setRunResult(prev => `${prev}\nPipeline complete. Items saved.`);
          setNodes(nds => nds.map(n => ({ ...n, data: { ...n.data, status: 'idle' } })));
        } else if (event.event === 'error') {
          setRunResult(prev => `${prev}\nError: ${JSON.stringify(event.errors)}`);
        }
      });
      
      setRunResult(prev => `${prev}\nFinal Result: ${JSON.stringify(result, null, 2)}`);
      
      // Update global items so UI reflects new generated content
      await fetchPipelineItems();
      await fetchKPIs();
    } catch (e) {
      setRunResult(`Error: ${e instanceof Error ? e.message : 'Backend offline'}`);
      setNodes(nds => nds.map(n => ({ ...n, data: { ...n.data, status: 'idle' } })));
    }
  };

  return (
    <div className="flex h-full" style={{ background: 'var(--bg-primary)' }}>
      {/* Sidebar controls */}
      <div className="w-72 flex-shrink-0 p-5 border-r overflow-y-auto" style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
        <h1 className="text-xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          Agent <span className="gradient-text">Console</span>
        </h1>
        <p className="text-xs mb-6" style={{ color: 'var(--text-muted)' }}>Visual n8n-style agent builder</p>

        {/* Add Node */}
        <div className="mb-6">
          <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
            Add Agent Node
          </div>
          <select
            id="agent-type-select"
            value={selectedAgent}
            onChange={e => setSelectedAgent(e.target.value as AgentType)}
            className="w-full px-3 py-2 rounded-xl text-sm mb-2 outline-none"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
          >
            {AGENT_TYPES.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
          <input
            id="agent-instruction-input"
            type="text"
            placeholder="Agent instruction..."
            value={instruction}
            onChange={e => setInstruction(e.target.value)}
            className="w-full px-3 py-2 rounded-xl text-sm mb-2 outline-none"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
          />
          <button id="add-node-btn" className="btn-primary w-full justify-center text-sm" onClick={addAgentNode}>
            <Plus size={13} /> Add Node
          </button>
        </div>

        {/* Delete */}
        <button id="delete-selected-btn" className="btn-ghost w-full justify-center text-sm mb-6" onClick={deleteSelected}>
          <Trash2 size={13} /> Delete Selected
        </button>

        {/* Run Custom */}
        <div className="mb-4">
          <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
            Run This Graph
          </div>
          <input
            id="custom-graph-goal"
            type="text"
            placeholder="Goal for this custom graph..."
            value={customGoal}
            onChange={e => setCustomGoal(e.target.value)}
            className="w-full px-3 py-2 rounded-xl text-sm mb-2 outline-none"
            style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
          />
          <button id="run-custom-graph-btn" className="btn-primary w-full justify-center text-sm" onClick={runCustomGraph}>
            <Play size={13} /> Execute Graph
          </button>
        </div>

        {runResult && (
          <div className="mt-4 p-3 rounded-xl text-xs font-mono overflow-auto max-h-48" style={{ background: 'rgba(0,0,0,0.3)', color: '#10b981' }}>
            {runResult}
          </div>
        )}

        {/* Legend */}
        <div className="mt-6">
          <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>Agents</div>
          {AGENT_TYPES.map(a => (
            <div key={a} className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full" style={{ background: AGENT_COLORS[a] }} />
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{a}</span>
              <span className="text-xs font-mono ml-auto" style={{ color: 'var(--text-muted)', fontSize: '10px' }}>{AGENT_MODELS[a]}</span>
            </div>
          ))}
        </div>
      </div>

      {/* React Flow canvas */}
      <div className="flex-1" id="agent-flow-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background color="rgba(255,255,255,0.03)" gap={24} />
          <Controls />
          <MiniMap
            nodeColor={n => AGENT_COLORS[(n.data as AgentNodeData).agent] || '#6366f1'}
            maskColor="rgba(8,12,20,0.8)"
          />
        </ReactFlow>
      </div>
    </div>
  );
}
