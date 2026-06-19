// TypeScript interfaces for CompanyOS V2

export type PipelineStatus = 'pending' | 'approved' | 'rejected' | 'scheduled' | 'posted' | 'vetoed';
export type AgentType = 'CEO' | 'CMO' | 'RESEARCH' | 'SDR' | 'AE' | 'ANALYST' | 'EMAIL' | 'RISK';
export type LeadStatus = 'new' | 'in_sequence' | 'booked' | 'closed' | 'lost';
export type BuyingStage = 'Awareness' | 'Consideration' | 'Decision' | 'Negotiation';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type ApprovalTier = 'AUTO_APPROVE' | 'MANAGER_APPROVAL' | 'CEO_APPROVAL';

export interface PipelineItem {
  id: string;
  agent_type: AgentType;
  status: PipelineStatus;
  title: string;
  content: string;
  platform: string;
  stage: string;
  meta_data: Record<string, unknown>;
  // V2 Brain Decision Framework fields
  confidence_score: number | null;
  risk_score: number | null;
  risk_level: RiskLevel | null;
  reasoning: string | null;
  alternatives_considered: string[];
  approval_tier: ApprovalTier | null;
  debate_log: string[];
  constitution_violations: string[];
  approval_required: boolean;
  // Timestamps
  created_at: string;
  updated_at: string;
  approved_at: string | null;
  scheduled_at: string | null;
  posted_at: string | null;
}

export interface Lead {
  id: string;
  status: LeadStatus;
  name: string;
  email: string | null;
  company: string | null;
  title: string | null;
  linkedin_url: string | null;
  buying_stage: BuyingStage;
  icp_score: number;
  touchpoints: number;
  notes: string | null;
  meta_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  last_contacted_at: string | null;
}

export interface AgentInfo {
  id: AgentType;
  name: string;
  model: string;
  role?: string;    // V2: role description
  status: 'idle' | 'working' | 'error';
}

export interface KPI {
  posts_this_week: number;
  active_leads: number;
  calls_booked: number;
  pending_review: number;
}

export interface VaultCollection {
  id: string;
  name: string;
  description: string;
  document_count: number;
}

export interface Analytics {
  weekly_reach: number;
  qualified_rate: number;
  reply_rate: number;
  total_leads: number;
  total_posts: number;
  weekly_posts: number;
}

// React Flow Agent Builder types
export interface AgentNodeData {
  agent: AgentType;
  instruction: string;
  config?: Record<string, unknown>;
  status?: 'idle' | 'working' | 'running' | 'done' | 'error';  // V2: unified status
  output?: Record<string, unknown>;
  // V2 Decision Framework fields (for displaying in nodes)
  confidence_score?: number;
  risk_level?: RiskLevel;
}

// V2: Brain Memory
export interface BrainMemory {
  agent_id: string;
  episodic_count: number;
  reflection_count: number;
  recent_episodes: Array<{
    timestamp: string;
    task: string;
    output_summary: string;
  }>;
  recent_reflections: Array<{
    timestamp: string;
    failure_reason: string;
    lesson: string;
  }>;
}

// V2: Activity Event for live feed
export interface ActivityEvent {
  id: string;
  timestamp: string;
  agent: string;
  event: string;
  details?: string;
  type: 'success' | 'warning' | 'error' | 'info';
}

