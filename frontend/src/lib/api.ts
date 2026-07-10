// API client for Sureflow backend
import axios from 'axios';
import type { PipelineItem, Lead, AgentInfo, KPI, VaultCollection, Analytics } from '@/types';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000, // 2 minutes — LLM calls can be slow
});

// ── Pipeline ──────────────────────────────────────────────────────────────────

export const pipelineApi = {
  run: async (
    goal: string, 
    lead_data?: Record<string, unknown>, 
    onEvent?: (event: any) => void
  ) => {
    const response = await fetch(`${api.defaults.baseURL}/pipeline/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal, lead_data }),
    });

    if (!response.body) throw new Error('No readable stream in response');

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let finalResult = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      
      // Keep the last incomplete chunk in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (onEvent) onEvent(data);
            if (data.event === 'complete') {
              finalResult = data;
            }
          } catch (e) {
            console.error("Failed to parse stream data chunk", line, e);
          }
        }
      }
    }
    return finalResult;
  },

  runCustom: async (
    graph_json: string, 
    goal: string, 
    lead_data?: Record<string, unknown>,
    onEvent?: (event: any) => void
  ) => {
    const response = await fetch(`${api.defaults.baseURL}/pipeline/custom`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ graph_json, goal, lead_data }),
    });

    if (!response.body) throw new Error('No readable stream in response');

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let finalResult = null;

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
            if (onEvent) onEvent(data);
            if (data.event === 'complete') {
              finalResult = data;
            }
          } catch (e) {
            console.error("Failed to parse stream data chunk", line, e);
          }
        }
      }
    }
    return finalResult;
  },

  getItems: (status?: string): Promise<PipelineItem[]> =>
    api.get('/pipeline/items', { params: status ? { status } : {} }).then(r => r.data),

  updateStatus: (id: string, status: string): Promise<PipelineItem> =>
    api.patch(`/pipeline/items/${id}/status`, { status }).then(r => r.data),

  getKPIs: (): Promise<KPI> =>
    api.get('/pipeline/kpis').then(r => r.data),
};

// ── Leads ────────────────────────────────────────────────────────────────────

export const leadsApi = {
  getAll: (status?: string): Promise<Lead[]> =>
    api.get('/leads', { params: status ? { status } : {} }).then(r => r.data),

  create: (data: Partial<Lead>): Promise<Lead> =>
    api.post('/leads', data).then(r => r.data),

  update: (id: string, data: Partial<Lead>): Promise<Lead> =>
    api.patch(`/leads/${id}`, data).then(r => r.data),

  score: (id: string) =>
    api.post(`/leads/${id}/score`).then(r => r.data),
};

// ── Agents ───────────────────────────────────────────────────────────────────

export const agentsApi = {
  getStatus: (): Promise<{ agents: AgentInfo[] }> =>
    api.get('/agents/status').then(r => r.data),
};

// ── Knowledge Vault ───────────────────────────────────────────────────────────

export const vaultApi = {
  getStats: (): Promise<{ collections: VaultCollection[] }> =>
    api.get('/vault/stats').then(r => r.data),

  ingest: (collection: string, file: File) => {
    const form = new FormData();
    form.append('collection', collection);
    form.append('file', file);
    return api.post('/vault/ingest', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data);
  },

  query: (collection: string, query: string, n_results = 5) =>
    api.post('/vault/query', { collection, query, n_results }).then(r => r.data),
};

// ── Analytics ────────────────────────────────────────────────────────────────

export const analyticsApi = {
  get: (): Promise<Analytics> =>
    api.get('/analytics').then(r => r.data),
};

// ── SSE helper (Phase 5) ──────────────────────────────────────────────────────
// Shared reader loop for `data: {...}\n\n` SSE streams, mirroring the pattern
// already used by pipelineApi.run/runCustom above. Returns the terminal
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

// ── Industrial Intelligence (Phase 4) ────────────────────────────────────────

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
  copilot: (query: string, conversation_history: Array<{ role: string; content: string }> = []): Promise<CopilotResponse> =>
    api.post('/industrial/copilot', { query, conversation_history }).then(r => r.data),

  // Streams stage events (Phase 5) as the Copilot works, resolving with the
  // same shape as `copilot()` once the `complete` event arrives.
  copilotStream: (
    query: string,
    conversation_history: Array<{ role: string; content: string }> = [],
    onEvent?: (event: any) => void,
  ): Promise<CopilotResponse> =>
    streamSSE(
      `${api.defaults.baseURL}/industrial/copilot/stream`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, conversation_history }),
      },
      onEvent || (() => {}),
    ).then(result => {
      if (!result || result.event === 'error') throw new Error(result?.detail || 'Copilot query failed');
      return result;
    }),

  // ── Document Upload ──
  uploadDocument: (file: File, doc_type: string = 'unknown', collection: string = ''): Promise<DocumentUploadResult> => {
    const form = new FormData();
    form.append('file', file);
    form.append('doc_type', doc_type);
    form.append('collection', collection);
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
    return streamSSE(
      `${api.defaults.baseURL}/industrial/upload/stream`,
      { method: 'POST', body: form },
      onEvent || (() => {}),
    ).then(result => {
      if (!result || result.event === 'error') throw new Error(result?.detail || 'Upload failed');
      return result;
    });
  },

  // ── Knowledge Graph ──
  getHierarchy: (): Promise<{ hierarchy: PlantHierarchyNode[] }> =>
    api.get('/industrial/graph/hierarchy').then(r => r.data),

  getEquipment: (): Promise<{ equipment: Equipment[] }> =>
    api.get('/industrial/graph/equipment').then(r => r.data),

  getEquipmentDetail: (tag: string): Promise<Equipment & Record<string, unknown>> =>
    api.get(`/industrial/graph/equipment/${tag}`).then(r => r.data),

  getTimeline: (tag: string, limit: number = 20): Promise<{ equipment_tag: string; timeline: AssetTimelineEvent[] }> =>
    api.get(`/industrial/graph/equipment/${tag}/timeline`, { params: { limit } }).then(r => r.data),

  getIncidents: (limit: number = 50): Promise<{ incidents: Incident[] }> =>
    api.get('/industrial/graph/incidents', { params: { limit } }).then(r => r.data),

  getOverview: (): Promise<{ overview: GraphOverview }> =>
    api.get('/industrial/graph/overview').then(r => r.data),

  getComplianceGaps: (area_id: string) =>
    api.get(`/industrial/graph/compliance-gaps/${area_id}`).then(r => r.data),

  // ── KPIs ──
  getKPIs: (): Promise<IndustrialKPIs> =>
    api.get('/industrial/kpis').then(r => r.data),

  // ── Agent Analysis ──
  analyzeMaintenance: (equipment_tag: string, analysis_type: string = 'full', incident_context: string = ''): Promise<MaintenanceResult> =>
    api.post('/industrial/maintenance/analyze', { equipment_tag, analysis_type, incident_context }).then(r => r.data),

  analyzeCompliance: (scope: string = 'facility', area_id: string = '', equipment_tag: string = '', regulation_focus: string = ''): Promise<ComplianceResult> =>
    api.post('/industrial/compliance/audit', { scope, area_id, equipment_tag, regulation_focus }).then(r => r.data),

  analyzeLessons: (incident_text: string = '', equipment_tag: string = '', incident_id: string = '', analysis_scope: string = 'single'): Promise<LessonsLearnedResult> =>
    api.post('/industrial/lessons-learned', { incident_text, equipment_tag, incident_id, analysis_scope }).then(r => r.data),

  // ── Work Orders ──
  createWorkOrder: (data: { title: string; description?: string; equipment_tag: string; type?: string; assigned_to?: string; status?: string; incident_id?: string }): Promise<{ status: string; wo_id: string; equipment_tag: string }> =>
    api.post('/industrial/work-orders', data).then(r => r.data),

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
