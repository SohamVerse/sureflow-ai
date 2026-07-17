// API client for SureFlow Industrial Intelligence backend
import axios from 'axios';
import type { AgentInfo } from '@/types';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000, // 2 minutes — LLM calls can be slow
});

// Attach the JWT (set at login) to every request. The backend derives the
// caller's role + plant scope from this token — see MULTI_LOCATION.md.
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('sureflow_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Bearer header for the raw fetch() SSE streams (axios interceptors don't cover them).
function authHeaders(): Record<string, string> {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('sureflow_token');
    if (token) return { Authorization: `Bearer ${token}` };
  }
  return {};
}

// The CTO's currently-selected plant (from the plant switcher). Plant users are
// forced to their own plant server-side, so this only applies to a CTO; when
// unset the CTO gets the global (all-plants) view.
export function activePlantId(): string | undefined {
  if (typeof window === 'undefined') return undefined;
  try {
    const u = JSON.parse(localStorage.getItem('sureflow_user') || 'null');
    if (u && u.role === 'cto') return localStorage.getItem('sureflow_target_plant') || undefined;
  } catch { /* ignore */ }
  return undefined;
}

function plantParams(): Record<string, string> {
  const p = activePlantId();
  return p ? { plant: p } : {};
}

// ── HQ (CTO only) ─────────────────────────────────────────────────────────────

export const hqApi = {
  overview: (): Promise<{ total_plants: number; totals: Record<string, number>; plants: any[]; highest_risk_plant: string | null }> =>
    api.get('/hq/overview').then(r => r.data),
  compare: (plantIds: string[]): Promise<{ comparison: any[] }> =>
    api.get('/hq/compare', { params: { plants: plantIds.join(',') } }).then(r => r.data),
  benchmark: (): Promise<{ ranking: any[] }> =>
    api.get('/hq/benchmark').then(r => r.data),
  // Global Copilot — always queries across ALL plants (ignores the switcher).
  copilot: (query: string, conversation_history: Array<{ role: string; content: string }> = []): Promise<any> =>
    api.post('/industrial/copilot', { query, conversation_history, target_plant_id: null }).then(r => r.data),
};

// ── System / analytics (ROADMAP §1) ───────────────────────────────────────────

export const systemApi = {
  aiQuality: (): Promise<{ agents: any[]; recent: any[]; totals: Record<string, number> }> =>
    api.get('/system/ai-quality').then(r => r.data),
  trends: (days = 120): Promise<{ scope: string; snapshots: any[] }> =>
    api.get('/industrial/kpis/trends', { params: { days, ...plantParams() } }).then(r => r.data),
  search: (q: string): Promise<{ query: string; equipment: any[]; incidents: any[]; documents: any[]; lessons: any[] }> =>
    api.get('/industrial/search', { params: { q, ...plantParams() } }).then(r => r.data),
  exportCsv: async (kind: 'equipment' | 'incidents' | 'work-orders'): Promise<void> => {
    const res = await api.get(`/industrial/export/${kind}.csv`, { params: plantParams(), responseType: 'blob' });
    const url = URL.createObjectURL(res.data as Blob);
    const a = document.createElement('a');
    a.href = url; a.download = `${kind}.csv`; a.click();
    URL.revokeObjectURL(url);
  },
};

// ── Alerts (ROADMAP §1 — proactive notifications) ─────────────────────────────

export const alertsApi = {
  list: (status?: string): Promise<{ alerts: any[] }> =>
    api.get('/alerts', { params: { ...plantParams(), ...(status ? { status } : {}) } }).then(r => r.data),
  digest: (): Promise<{ scope: string; headline: string; open_total: number; critical: number; high: number; priorities: any[] }> =>
    api.get('/alerts/digest', { params: plantParams() }).then(r => r.data),
  count: (): Promise<{ count: number }> =>
    api.get('/alerts/count', { params: plantParams() }).then(r => r.data),
  generate: (): Promise<{ created: number }> =>
    api.post('/alerts/generate', null, { params: plantParams() }).then(r => r.data),
  ack: (id: string): Promise<any> => api.post(`/alerts/${id}/ack`).then(r => r.data),
  resolve: (id: string): Promise<any> => api.post(`/alerts/${id}/resolve`).then(r => r.data),
};

export const plantsApi = {
  list: (): Promise<{ plants: any[] }> => api.get('/plants').then(r => r.data),
  create: (payload: {
    plant_id?: string; name: string; location?: string;
    areas?: Array<{ area_id: string; name: string }>;
    manager?: { email: string; password: string; name?: string };
  }): Promise<any> => api.post('/plants', payload).then(r => r.data),
};

// ── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string): Promise<{ access_token: string; user: { email: string; name: string; role: string; plant_id: string | null } }> =>
    api.post('/auth/login', { email, password }).then(r => r.data),
  me: (): Promise<{ user: { email: string; name: string; role: string; plant_id: string | null }; plants: Array<{ plant_id: string; name: string; location: string }> }> =>
    api.get('/auth/me').then(r => r.data),
};

// ── Agents ───────────────────────────────────────────────────────────────────

export const agentsApi = {
  getStatus: (): Promise<{ agents: AgentInfo[] }> =>
    api.get('/agents/status').then(r => r.data),
};

// ── SSE helper (Phase 5) ──────────────────────────────────────────────────────
// Shared reader loop for `data: {...}\n\n` SSE streams. Returns the terminal
// `complete`/`error` event, while forwarding every event to onEvent as it
// arrives so callers can render live stage progress.
async function streamSSE(
  url: string,
  options: RequestInit,
  onEvent: (event: any) => void,
): Promise<any> {
  const response = await fetch(url, options);
  if (!response.body) throw new Error('No readable stream in response');

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let finalResult: any = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          onEvent(data);
          if (data.event === 'complete' || data.event === 'error') finalResult = data;
        } catch (e) {
          console.error('Failed to parse stream data chunk', line, e);
        }
      }
    }
  }
  return finalResult;
}

// ── Industrial Intelligence ───────────────────────────────────────────────────

import type {
  IndustrialKPIs,
  CopilotResponse,
  MaintenanceResult,
  ComplianceResult,
  LessonsLearnedResult,
  DocumentUploadResult,
  SensorData,
  IndustrialVaultCollection,
  Equipment,
  Incident,
  AssetTimelineEvent,
  PlantHierarchyNode,
  GraphOverview,
  WorkOrder,
} from '@/types';

export const industrialApi = {
  // ── Copilot ──
  copilot: (query: string, conversation_history: Array<{ role: string; content: string }> = []): Promise<CopilotResponse> => {
    let user_role = 'cto';
    let user_plant_id = undefined;
    let target_plant_id = undefined;
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('sureflow_user');
      if (stored) {
        const u = JSON.parse(stored);
        user_role = u.role || 'cto';
        user_plant_id = u.plantId;
      }
      target_plant_id = localStorage.getItem('sureflow_target_plant') || undefined;
    }
    return api.post('/industrial/copilot', { query, conversation_history, user_role, user_plant_id, target_plant_id }).then(r => r.data);
  },

  // Streams stage events (Phase 5) as the Copilot works, resolving with the
  // same shape as `copilot()` once the `complete` event arrives.
  copilotStream: (
    query: string,
    conversation_history: Array<{ role: string; content: string }> = [],
    onEvent?: (event: any) => void,
  ): Promise<CopilotResponse> => {
    let user_role = 'cto';
    let user_plant_id = undefined;
    let target_plant_id = undefined;
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('sureflow_user');
      if (stored) {
        const u = JSON.parse(stored);
        user_role = u.role || 'cto';
        user_plant_id = u.plantId;
      }
      target_plant_id = localStorage.getItem('sureflow_target_plant') || undefined;
    }
    return streamSSE(
      `${api.defaults.baseURL}/industrial/copilot/stream`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ query, conversation_history, user_role, user_plant_id, target_plant_id }),
      },
      onEvent || (() => {}),
    ).then(result => {
      if (!result || result.event === 'error') throw new Error(result?.detail || 'Copilot query failed');
      return result;
    });
  },

  // ── Document Upload ──
  uploadDocument: (file: File, doc_type: string = 'unknown', collection: string = ''): Promise<DocumentUploadResult> => {
    const form = new FormData();
    form.append('file', file);
    form.append('doc_type', doc_type);
    form.append('collection', collection);
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('sureflow_user');
      if (stored) {
        const u = JSON.parse(stored);
        if (u.plantId) form.append('plant_id', u.plantId);
      }
    }
    return api.post('/industrial/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5 min for large docs
    }).then(r => r.data);
  },

  // Streams stage events (Phase 5) as the ingestion pipeline runs, resolving
  // with the same shape as `uploadDocument()` once the `complete` event arrives.
  uploadDocumentStream: (
    file: File,
    doc_type: string = 'unknown',
    onEvent?: (event: any) => void,
    collection: string = '',
  ): Promise<DocumentUploadResult> => {
    const form = new FormData();
    form.append('file', file);
    form.append('doc_type', doc_type);
    form.append('collection', collection);
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('sureflow_user');
      if (stored) {
        const u = JSON.parse(stored);
        if (u.plantId) {
          form.append('plant_id', u.plantId);
        }
      }
    }
    return streamSSE(
      `${api.defaults.baseURL}/industrial/upload/stream`,
      { method: 'POST', body: form, headers: authHeaders() },
      onEvent || (() => {}),
    ).then(result => {
      if (!result || result.event === 'error') throw new Error(result?.detail || 'Upload failed');
      return result;
    });
  },

  // ── Knowledge Graph (plant-scoped for CTO via the `plant` param) ──
  getHierarchy: (): Promise<{ hierarchy: PlantHierarchyNode[] }> =>
    api.get('/industrial/graph/hierarchy', { params: plantParams() }).then(r => r.data),

  getEquipment: (): Promise<{ equipment: Equipment[] }> =>
    api.get('/industrial/graph/equipment', { params: plantParams() }).then(r => r.data),

  getEquipmentDetail: (tag: string): Promise<Equipment & Record<string, unknown>> =>
    api.get(`/industrial/graph/equipment/${tag}`).then(r => r.data),

  getTimeline: (tag: string, limit: number = 20): Promise<{ equipment_tag: string; timeline: AssetTimelineEvent[] }> =>
    api.get(`/industrial/graph/equipment/${tag}/timeline`, { params: { limit } }).then(r => r.data),

  getIncidents: (limit: number = 50): Promise<{ incidents: Incident[] }> =>
    api.get('/industrial/graph/incidents', { params: { limit, ...plantParams() } }).then(r => r.data),

  getOverview: (): Promise<{ overview: GraphOverview }> =>
    api.get('/industrial/graph/overview', { params: plantParams() }).then(r => r.data),

  getComplianceGaps: (area_id: string) =>
    api.get(`/industrial/graph/compliance-gaps/${area_id}`).then(r => r.data),

  // ── KPIs ──
  getKPIs: (): Promise<IndustrialKPIs> =>
    api.get('/industrial/kpis', { params: plantParams() }).then(r => r.data),

  // ── Agent Analysis (target_plant_id lets a CTO scope to the active plant) ──
  analyzeMaintenance: (equipment_tag: string, analysis_type: string = 'full', incident_context: string = ''): Promise<MaintenanceResult> =>
    api.post('/industrial/maintenance/analyze', { equipment_tag, analysis_type, incident_context, target_plant_id: activePlantId() }).then(r => r.data),

  analyzeCompliance: (scope: string = 'facility', area_id: string = '', equipment_tag: string = '', regulation_focus: string = ''): Promise<ComplianceResult> =>
    api.post('/industrial/compliance/audit', { scope, area_id, equipment_tag, regulation_focus, target_plant_id: activePlantId() }).then(r => r.data),

  analyzeLessons: (incident_text: string = '', equipment_tag: string = '', incident_id: string = '', analysis_scope: string = 'single'): Promise<LessonsLearnedResult> =>
    api.post('/industrial/lessons-learned', { incident_text, equipment_tag, incident_id, analysis_scope, target_plant_id: activePlantId() }).then(r => r.data),

  // ── Work Orders (closed-loop) ──
  getWorkOrders: (): Promise<{ work_orders: any[] }> =>
    api.get('/industrial/work-orders', { params: plantParams() }).then(r => r.data),

  createWorkOrder: (data: { title: string; description?: string; equipment_tag: string; type?: string; assigned_to?: string; status?: string; incident_id?: string }): Promise<{ status: string; wo_id: string; equipment_tag: string }> =>
    api.post('/industrial/work-orders', { ...data, target_plant_id: activePlantId() }).then(r => r.data),

  updateWorkOrderStatus: (wo_id: string, status: string): Promise<any> =>
    api.post(`/industrial/work-orders/${wo_id}/status`, { status }).then(r => r.data),

  // ── Sensors (Mock IoT) ──
  getSensorData: (equipment_tag: string): Promise<SensorData> =>
    api.get(`/industrial/mcp/sensor/${equipment_tag}`).then(r => r.data),

  // ── Vault ──
  getVaultStats: (): Promise<{ collections: IndustrialVaultCollection[] }> =>
    api.get('/industrial/vault/stats').then(r => r.data),

  // ── CMMS (Mock) ──
  getCMMSEquipment: (tag: string) =>
    api.get(`/industrial/mcp/cmms/equipment/${tag}`).then(r => r.data),
};

export default api;
