import { create } from 'zustand';
import toast from 'react-hot-toast';
import type { PipelineItem, Lead, AgentInfo, KPI, VaultCollection, Analytics, Equipment, Incident, PlantHierarchyNode, GraphOverview, IndustrialKPIs, CopilotMessage, SensorData } from '@/types';
import { pipelineApi, leadsApi, agentsApi, vaultApi, analyticsApi, industrialApi } from '@/lib/api';

interface SureflowStore {
  // Pipeline
  pipelineItems: PipelineItem[];
  loadingPipeline: boolean;
  fetchPipelineItems: (status?: string) => Promise<void>;
  updateItemStatus: (id: string, status: string) => Promise<void>;
  runPipeline: (goal: string, leadData?: Record<string, unknown>) => Promise<void>;
  pipelineRunning: boolean;
  lastRunResult: Record<string, unknown> | null;

  // Leads
  leads: Lead[];
  loadingLeads: boolean;
  fetchLeads: (status?: string) => Promise<void>;
  createLead: (data: Partial<Lead>) => Promise<void>;
  updateLead: (id: string, data: Partial<Lead>) => Promise<void>;
  scoreLead: (id: string) => Promise<void>;

  // Agents
  agents: AgentInfo[];
  fetchAgents: () => Promise<void>;
  setAgentStatus: (id: string, status: AgentInfo['status']) => void;

  // KPIs
  kpis: KPI | null;
  fetchKPIs: () => Promise<void>;

  // Vault
  vaultCollections: VaultCollection[];
  fetchVaultStats: () => Promise<void>;

  // Analytics
  analytics: Analytics | null;
  fetchAnalytics: () => Promise<void>;

  // V2: Approval Center
  pendingApprovals: number;
  approvalItems: PipelineItem[];
  fetchPendingApprovals: () => Promise<void>;
  approveItem: (id: string) => Promise<void>;
  rejectItem: (id: string) => Promise<void>;

  // V2: Activity Feed (real-time log of agent events)
  activityFeed: ActivityEvent[];
  addActivityEvent: (event: ActivityEvent) => void;

  // Industrial Intelligence (Phase 4)
  industrialEquipment: Equipment[];
  industrialHierarchy: PlantHierarchyNode[];
  industrialOverview: GraphOverview | null;
  industrialIncidents: Incident[];
  industrialKPIs: IndustrialKPIs | null;
  copilotMessages: CopilotMessage[];
  copilotLoading: boolean;
  copilotStage: string | null;
  selectedEquipmentTag: string | null;
  sensorData: SensorData | null;
  loadingIndustrial: boolean;
  fetchIndustrialEquipment: () => Promise<void>;
  fetchIndustrialHierarchy: () => Promise<void>;
  fetchIndustrialOverview: () => Promise<void>;
  fetchIndustrialIncidents: () => Promise<void>;
  fetchIndustrialKPIs: () => Promise<void>;
  sendCopilotMessage: (query: string) => Promise<void>;
  clearCopilotMessages: () => void;
  fetchSensorData: (tag: string) => Promise<void>;
  setSelectedEquipmentTag: (tag: string | null) => void;

  // Global
  error: string | null;
  clearError: () => void;
}

export interface ActivityEvent {
  id: string;
  timestamp: string;
  agent: string;
  event: string;
  details?: string;
  type: 'success' | 'warning' | 'error' | 'info';
}


export const useSureflowStore = create<SureflowStore>((set, get) => ({
  // ── Pipeline ────────────────────────────────────────────────────────────────
  pipelineItems: [],
  loadingPipeline: false,
  pipelineRunning: false,
  lastRunResult: null,

  fetchPipelineItems: async (status) => {
    set({ loadingPipeline: true });
    try {
      const items = await pipelineApi.getItems(status);
      set({ pipelineItems: items, loadingPipeline: false });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      set({ error: `Failed to load pipeline: ${msg}`, loadingPipeline: false });
    }
  },

  updateItemStatus: async (id, status) => {
    try {
      const updated = await pipelineApi.updateStatus(id, status);
      set(state => ({
        pipelineItems: state.pipelineItems.map(i => i.id === id ? updated : i),
      }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      set({ error: `Failed to update status: ${msg}` });
    }
  },

  runPipeline: async (goal, leadData) => {
    set({ pipelineRunning: true, error: null });
    // Set only CEO to working initially
    set(state => ({
      agents: state.agents.map(a => ({ ...a, status: a.id === 'CEO' ? 'working' : 'idle' })),
    }));
    
    toast.success('Pipeline Triggered! Agents are working...', { icon: '🚀' });

    try {
      const result = await pipelineApi.run(goal, leadData, (event) => {
        if (event.event === 'agent_update') {
          const nodeName = event.node;
          if (nodeName === 'ceo') {
            get().setAgentStatus('CEO', 'idle');
            const plan = event.update?.ceo_plan;
            if (plan && plan.tasks) {
              const nextAgents = plan.tasks.map((t: any) => t.agent.toUpperCase());
              set(state => ({
                agents: state.agents.map(a => ({
                  ...a,
                  status: nextAgents.includes(a.id) ? 'working' : a.status
                }))
              }));
            }
          } else if (nodeName !== 'finalize') {
            const agentId = nodeName.toUpperCase();
            toast.success(`${agentId} completed task!`, { icon: '⚡️' });
            get().setAgentStatus(agentId, 'idle');
            
            // SDR always transitions to AE in our graph
            if (nodeName === 'sdr') {
              get().setAgentStatus('AE', 'working');
            }
          }
        } else if (event.event === 'complete') {
          toast.success('Pipeline finished and saved to database.', { icon: '✅' });
        }
      });
      
      set({ lastRunResult: result, pipelineRunning: false });
      await get().fetchPipelineItems();
      await get().fetchKPIs();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      toast.error(`Pipeline failed: ${msg}`);
      set({ error: `Pipeline failed: ${msg}`, pipelineRunning: false });
    } finally {
      set(state => ({
        agents: state.agents.map(a => ({ ...a, status: 'idle' as const })),
      }));
    }
  },

  // ── Leads ────────────────────────────────────────────────────────────────────
  leads: [],
  loadingLeads: false,

  fetchLeads: async (status) => {
    set({ loadingLeads: true });
    try {
      const leads = await leadsApi.getAll(status);
      set({ leads, loadingLeads: false });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      set({ error: `Failed to load leads: ${msg}`, loadingLeads: false });
    }
  },

  createLead: async (data) => {
    try {
      const lead = await leadsApi.create(data);
      set(state => ({ leads: [lead, ...state.leads] }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      set({ error: `Failed to create lead: ${msg}` });
    }
  },

  updateLead: async (id, data) => {
    try {
      const updated = await leadsApi.update(id, data);
      set(state => ({ leads: state.leads.map(l => l.id === id ? updated : l) }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      set({ error: `Failed to update lead: ${msg}` });
    }
  },

  scoreLead: async (id) => {
    try {
      const result = await leadsApi.score(id);
      set(state => ({ leads: state.leads.map(l => l.id === id ? result.lead : l) }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      set({ error: `Failed to score lead: ${msg}` });
    }
  },

  // ── Agents ────────────────────────────────────────────────────────────────────
  agents: [],
  fetchAgents: async () => {
    try {
      const { agents } = await agentsApi.getStatus();
      if (get().pipelineRunning) {
        // Prevent backend from resetting UI to idle while pipeline is executing
        // Merge models but keep local status
        set(state => ({
          agents: agents.map((a: AgentInfo) => {
            const existing = state.agents.find(ea => ea.id === a.id);
            return { ...a, status: existing ? existing.status : 'idle' };
          })
        }));
      } else {
        set({ agents });
      }
    } catch { /* Silently fail if backend offline */ }
  },
  setAgentStatus: (id, status) => {
    set(state => ({
      agents: state.agents.map(a => a.id === id ? { ...a, status } : a),
    }));
  },

  // ── KPIs ─────────────────────────────────────────────────────────────────────
  kpis: null,
  fetchKPIs: async () => {
    try {
      const kpis = await pipelineApi.getKPIs();
      set({ kpis });
    } catch { /* Silently fail */ }
  },

  // ── Vault ────────────────────────────────────────────────────────────────────
  vaultCollections: [],
  fetchVaultStats: async () => {
    try {
      const { collections } = await vaultApi.getStats();
      set({ vaultCollections: collections });
    } catch { /* Silently fail */ }
  },

  // ── Analytics ────────────────────────────────────────────────────────────────
  analytics: null,
  fetchAnalytics: async () => {
    try {
      const analytics = await analyticsApi.get();
      set({ analytics });
    } catch { /* Silently fail */ }
  },

  // ── Global ───────────────────────────────────────────────────────────────────
  error: null,
  clearError: () => set({ error: null }),

  // ── V2: Approval Center ───────────────────────────────────────────────────────
  pendingApprovals: 0,
  approvalItems: [],

  fetchPendingApprovals: async () => {
    try {
      const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${BASE}/approvals`);
      if (!res.ok) return;
      const items = await res.json();
      set({ approvalItems: items, pendingApprovals: items.length });
    } catch { /* Silently fail */ }
  },

  approveItem: async (id: string) => {
    try {
      const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${BASE}/approvals/${id}/approve`, { method: 'POST' });
      if (!res.ok) throw new Error('Approval failed');
      toast.success('Item approved ✅');
      set(state => ({
        approvalItems: state.approvalItems.filter(i => i.id !== id),
        pendingApprovals: Math.max(0, state.pendingApprovals - 1),
      }));
      get().fetchPipelineItems();
    } catch (e: unknown) {
      toast.error('Approval failed');
    }
  },

  rejectItem: async (id: string) => {
    try {
      const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${BASE}/approvals/${id}/reject`, { method: 'POST' });
      if (!res.ok) throw new Error('Rejection failed');
      toast.success('Item rejected 🚫');
      set(state => ({
        approvalItems: state.approvalItems.filter(i => i.id !== id),
        pendingApprovals: Math.max(0, state.pendingApprovals - 1),
      }));
    } catch (e: unknown) {
      toast.error('Rejection failed');
    }
  },

  // ── V2: Activity Feed ─────────────────────────────────────────────────────────
  activityFeed: [],

  addActivityEvent: (event) => {
    set(state => ({
      activityFeed: [event, ...state.activityFeed].slice(0, 100), // Keep last 100 events
    }));
  },

  // ── Industrial Intelligence (Phase 4) ──────────────────────────────────────────
  industrialEquipment: [],
  industrialHierarchy: [],
  industrialOverview: null,
  industrialIncidents: [],
  industrialKPIs: null,
  copilotMessages: [],
  copilotLoading: false,
  copilotStage: null,
  selectedEquipmentTag: null,
  sensorData: null,
  loadingIndustrial: false,

  fetchIndustrialEquipment: async () => {
    set({ loadingIndustrial: true });
    try {
      const { equipment } = await industrialApi.getEquipment();
      set({ industrialEquipment: equipment, loadingIndustrial: false });
    } catch { set({ loadingIndustrial: false }); }
  },

  fetchIndustrialHierarchy: async () => {
    try {
      const { hierarchy } = await industrialApi.getHierarchy();
      set({ industrialHierarchy: hierarchy });
    } catch { /* silently fail */ }
  },

  fetchIndustrialOverview: async () => {
    try {
      const { overview } = await industrialApi.getOverview();
      set({ industrialOverview: overview });
    } catch { /* silently fail */ }
  },

  fetchIndustrialIncidents: async () => {
    try {
      const { incidents } = await industrialApi.getIncidents();
      set({ industrialIncidents: incidents });
    } catch { /* silently fail */ }
  },

  fetchIndustrialKPIs: async () => {
    try {
      const kpis = await industrialApi.getKPIs();
      set({ industrialKPIs: kpis });
    } catch { /* silently fail */ }
  },

  sendCopilotMessage: async (query: string) => {
    const userMsg: CopilotMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };
    set(state => ({
      copilotMessages: [...state.copilotMessages, userMsg],
      copilotLoading: true,
      copilotStage: null,
    }));

    try {
      const history = get().copilotMessages
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .map(m => ({ role: m.role, content: m.content }));
      const response = await industrialApi.copilotStream(query, history, event => {
        if (event.event === 'stage') set({ copilotStage: event.label || event.stage });
      });
      const aiMsg: CopilotMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: response.answer || ((response as unknown as Record<string, string>).summary) || JSON.stringify(response),
        timestamp: new Date().toISOString(),
        citations: response.citations,
        sources: response.sources_used,
        sources_consulted: response.sources_consulted,
        safety_alerts: response.safety_alerts,
        follow_up_questions: response.follow_up_questions,
        reasoning: response.reasoning,
        confidence: response.confidence,
        risk_level: response.risk_level,
        self_challenge: response.self_challenge,
      };
      set(state => ({
        copilotMessages: [...state.copilotMessages, aiMsg],
        copilotLoading: false,
        copilotStage: null,
      }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Copilot error';
      const errorMsg: CopilotMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ Error: ${msg}. Please check that the backend is running.`,
        timestamp: new Date().toISOString(),
      };
      set(state => ({
        copilotMessages: [...state.copilotMessages, errorMsg],
        copilotLoading: false,
        copilotStage: null,
      }));
      toast.error(`Copilot error: ${msg}`);
    }
  },

  clearCopilotMessages: () => set({ copilotMessages: [] }),

  fetchSensorData: async (tag: string) => {
    try {
      const data = await industrialApi.getSensorData(tag);
      set({ sensorData: data, selectedEquipmentTag: tag });
    } catch { /* silently fail */ }
  },

  setSelectedEquipmentTag: (tag: string | null) => set({ selectedEquipmentTag: tag }),
}));
