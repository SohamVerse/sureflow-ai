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

export default api;
