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
  // Brain Decision Framework fields
  confidence: number | null;
  risk_score: number | null;
  risk_level: RiskLevel | null;
  reasoning: string | null;
  alternatives: string[];
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
  // Decision Framework fields (for displaying in nodes)
  confidence?: number;
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

// ── Industrial Intelligence Types (Phase 4) ─────────────────────────────────

export type EquipmentStatus = 'operational' | 'warning' | 'critical' | 'offline';

export interface Equipment {
  tag: string;
  name: string;
  type: string;
  area: string;
  area_id: string;
  status: EquipmentStatus;
  criticality: string;
  manufacturer?: string;
  model?: string;
  install_date?: string;
  last_maintenance?: string;
  mtbf_hours?: number;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: string;
  equipment_tag: string;
  date: string;
  root_cause?: string;
  lessons?: string[];
}

export interface WorkOrder {
  wo_id: string;
  title: string;
  description: string;
  equipment_tag: string;
  type: string;
  status: string;
  assigned_to: string;
  created_at: string;
  incident_id?: string;
}

export interface Inspection {
  id: string;
  equipment_tag: string;
  type: string;
  result: string;
  date: string;
  inspector: string;
  notes?: string;
}

export interface AssetTimelineEvent {
  type: 'incident' | 'work_order' | 'inspection';
  id: string;
  title: string;
  date: string;
  severity?: string;
  status?: string;
  description?: string;
}

export interface PlantHierarchyNode {
  id: string;
  name: string;
  type: 'plant' | 'area' | 'equipment';
  children?: PlantHierarchyNode[];
  tag?: string;
  status?: EquipmentStatus;
  equipment_count?: number;
}

export interface GraphOverview {
  plants: number;
  areas: number;
  equipment: number;
  incidents: number;
  work_orders: number;
  inspections: number;
  documents: number;
}

// Agent Reasoning (Phase 5) — every agent goes through the shared BaseBrain
// contract (backend/core/brain.py), so these fields are present on every
// industrial agent response, not just the Copilot's.
export interface AgentReasoning {
  reasoning?: string;
  confidence?: number;
  risk_level?: RiskLevel;
  alternatives?: string[];
  self_challenge?: string;
  recommendation?: string;
}

// Copilot
export interface CopilotMessage extends AgentReasoning {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: CopilotCitation[];
  sources?: string[];
  sources_consulted?: string[];
  safety_alerts?: string[];
  follow_up_questions?: string[];
  stage?: string;
}

export interface CopilotCitation {
  text: string;
  source: string;
  collection?: string;
  relevance?: number;
}

export interface CopilotResponse extends AgentReasoning {
  run_id: string;
  answer: string;
  citations: CopilotCitation[];
  sources_used: string[];
  sources_consulted?: string[];
  safety_alerts?: string[];
  follow_up_questions?: string[];
  confidence: number;
}

// Maintenance — shape matches agents/maintenance.py's MAINTENANCE_SYSTEM_PROMPT
// JSON schema exactly (verified against a live response, not assumed).
export interface MaintenanceRCA {
  root_cause: string;
  contributing_factors: string[];
  evidence?: string[];
  five_why_chain: string[];
  failure_mode?: string;
}

export interface MaintenancePrediction {
  equipment_tag: string;
  equipment_name?: string;
  failure_mode: string;
  probability: number; // 0-100
  timeframe: string;
  basis?: string;
}

export interface MaintenanceRecommendation {
  action: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  equipment_tag?: string;
  justification?: string;
  estimated_cost?: string;
  estimated_downtime?: string;
  failure_cost_if_ignored?: string;
}

export interface SimilarAssetAnalysis {
  assets_compared?: string[];
  common_failure_modes?: string[];
  mtbf_estimate_hours?: number;
  pattern_summary?: string;
}

export interface MaintenanceResult extends AgentReasoning {
  run_id: string;
  equipment_tag: string;
  analysis_type: string;
  rca?: MaintenanceRCA;
  predictions?: MaintenancePrediction[];
  recommendations?: MaintenanceRecommendation[];
  similar_asset_analysis?: SimilarAssetAnalysis;
  summary?: string;
}

// Compliance — shape matches agents/compliance.py's COMPLIANCE_SYSTEM_PROMPT
// JSON schema exactly (verified against a live response, not assumed).
export interface ComplianceGap {
  gap_id?: string;
  equipment_tag?: string;
  area?: string;
  regulation?: string;
  requirement?: string;
  current_state?: string;
  finding: string;
  severity: 'critical' | 'major' | 'minor' | 'observation';
  due_date?: string;
  evidence_available?: boolean;
  remediation?: string;
}

export interface AuditReadiness {
  overall_status: 'ready' | 'needs_work' | 'not_ready';
  areas_reviewed?: number;
  findings_count?: { critical: number; major: number; minor: number; observations: number };
  evidence_summary?: string;
  estimated_remediation_days?: number;
}

export interface SopGap {
  sop_title: string;
  regulatory_requirement?: string;
  status: 'adequate' | 'needs_update' | 'missing' | 'expired';
  finding?: string;
}

export interface ComplianceRecommendation {
  action: string;
  priority: 'immediate' | 'within_30_days' | 'within_90_days' | 'annual_review';
  regulation?: string;
  responsible_party?: string;
  deadline?: string;
}

export interface ComplianceResult extends AgentReasoning {
  run_id: string;
  scope: string;
  overall_compliance_status?: string;
  compliance_score?: number;
  gaps: ComplianceGap[];
  audit_readiness?: AuditReadiness;
  sop_gaps?: SopGap[];
  recommendations?: ComplianceRecommendation[];
  summary?: string;
}

// Lessons Learned — shape matches agents/lessons_learned.py's
// LESSONS_LEARNED_SYSTEM_PROMPT JSON schema exactly.
export interface LessonItem {
  lesson: string;
  equipment_tag?: string;
  incident_id?: string;
  category?: string;
  severity?: 'critical' | 'high' | 'medium' | 'low';
  root_cause?: string;
  corrective_action?: string;
  preventive_action?: string;
}

export interface LessonsWarning {
  target_equipment: string;
  risk_description: string;
  risk_level: 'critical' | 'high' | 'medium' | 'low';
  reason?: string;
  based_on_incident?: string;
  recommended_action?: string;
}

export interface LessonsPattern {
  pattern: string;
  frequency?: string;
  affected_assets?: string[];
  affected_vendors?: string[];
  trend?: 'increasing' | 'stable' | 'decreasing';
  systemic_recommendation?: string;
}

export interface LessonsLearnedResult extends AgentReasoning {
  run_id: string;
  lessons: LessonItem[];
  warnings?: LessonsWarning[];
  patterns?: LessonsPattern[];
  summary?: string;
}

// Sensors
export interface SensorReading {
  sensor_type: string;
  value: number;
  unit: string;
  timestamp: string;
  status: 'normal' | 'warning' | 'critical';
  threshold_low?: number;
  threshold_high?: number;
}

export interface SensorData {
  equipment_tag: string;
  readings: SensorReading[];
  alerts: SensorAlert[];
}

export interface SensorAlert {
  sensor_type: string;
  message: string;
  severity: 'warning' | 'critical';
  timestamp: string;
}

// Industrial KPIs
export interface IndustrialKPIs {
  graph_overview: GraphOverview;
  lessons_learned_count: number;
  safety_incidents: number;
}

// Document Upload
export interface DocumentUploadResult {
  status: string;
  run_id: string;
  file_name: string;
  doc_type: string;
  collection: string;
  pages_extracted: number;
  entities_found: number;
  relationships_found: number;
  chunks_embedded: number;
  graph_nodes_created: number;
  summary: string;
  doc_metadata: Record<string, unknown>;
}

// Industrial Vault
export interface IndustrialVaultCollection {
  id: string;
  name: string;
  description: string;
  document_count: number;
}

