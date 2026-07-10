import { create } from 'zustand';
import toast from 'react-hot-toast';
import type { AgentInfo, Equipment, Incident, PlantHierarchyNode, GraphOverview, IndustrialKPIs, CopilotMessage, SensorData } from '@/types';
import { agentsApi, industrialApi } from '@/lib/api';

interface SureflowStore {
  // Agents (Brain Status panel)
  agents: AgentInfo[];
  fetchAgents: () => Promise<void>;

  // Industrial Intelligence
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

export const useSureflowStore = create<SureflowStore>((set, get) => ({
  // ── Agents ────────────────────────────────────────────────────────────────────
  agents: [],
  fetchAgents: async () => {
    try {
      const { agents } = await agentsApi.getStatus();
      set({ agents });
    } catch { /* Silently fail if backend offline */ }
  },

  // ── Global ───────────────────────────────────────────────────────────────────
  error: null,
  clearError: () => set({ error: null }),

  // ── Industrial Intelligence ─────────────────────────────────────────────────
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
