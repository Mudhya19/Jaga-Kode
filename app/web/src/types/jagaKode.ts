export type RiskCategory = 'HIGH_RISK' | 'MEDIUM_RISK' | 'LOW_RISK';

export type VerifierDecision =
  | 'APPROVED'
  | 'PENDING_CLARIFICATION'
  | 'PENDING_VERIFICATION'
  | 'REJECTED_UPCODING';

export type PresetCaseKey =
  | 'clean_normal'
  | 'ghost_comorbidity'
  | 'severity_jump'
  | 'los_inflation'
  | 'unbundling';

export interface HealthStatusResponse {
  status: string;
  version: string;
  project: string;
  models_loaded: boolean;
  peer_profiles_count: number;
  environment: string;
}

export interface SingleClaimInput {
  FKL02: string;
  FKL07: number;
  FKL08: number;
  FKL09: number;
  FKL10: number;
  FKL14: number;
  FKL15A?: string | null;
  FKL17A: string;
  FKL18?: string | null;
  FKL19: string;
  FKL20: number;
  FKL21: number;
  FKL23: number;
  FKL31: number;
  FKL32?: number | null;
  FKL33?: number | null;
  FKL47: number;
  FKL48?: number | null;
  los: number;
  secondary_diagnoses: string[];
  peer_group_id?: string | null;
}

export interface RadarDimensions {
  los_deviation: number;
  cost_deviation: number;
  comorbidity_intensity: number;
  severity_level: number;
  regulatory_violation: number;
}

export interface ClaimEvaluationResponse {
  claim_id: string;
  risk_index: number;
  risk_category: RiskCategory;
  badge_color: string;
  primary_driver: string;
  recommended_action: string;
  rule_risk_score: number;
  ml_anomaly_score: number;
  rule_violations: string[];
  radar: RadarDimensions;
  clinical_narrative: string[];
  explanation_text?: string;
  cost_peer_ratio: number;
  los_peer_zscore: number;
  comorbidity_count: number;
  has_severe_comorbidity: number;
  // Claim context metadata
  FKL07?: number;
  FKL08?: number;
  FKL09?: number;
  FKL10?: number;
  FKL14?: number;
  FKL15A?: string;
  FKL17A?: string;
  FKL18?: string;
  FKL19?: string;
  FKL20?: number;
  FKL21?: number;
  FKL23?: number;
  severity_level?: number;
  FKL31?: number;
  FKL32?: number;
  FKL33?: number;
  FKL47?: number;
  los?: number;
  peer_group_id?: string;
  secondary_diagnoses?: string[];
  plausibility_score?: number;
  unbundling_index?: number;
}

export interface BatchEvaluationSummary {
  total_claims: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  total_billed_idr: number;
  high_risk_billed_idr?: number;
  total_disputed_potential_idr: number;
  fast_track_percentage: number;
  results: ClaimEvaluationResponse[];
}

export interface PeerProfileMetrics {
  count?: number;
  mean_los?: number;
  std_los?: number;
  median_cost?: number;
  iqr_cost?: number;
  mean_comorbidity?: number;
  std_comorbidity?: number;
  severity_3_ratio?: number;
}

export interface PeerGroupStatsResponse {
  peer_group_id: string | null;
  cmg: number | null;
  resolution_level: string;
  profile: PeerProfileMetrics;
  total_peer_cmg_profiles: number;
  total_peer_groups?: number;
  global_profile: PeerProfileMetrics;
}

export interface AuditActionRequest {
  claim_id: string;
  decision: VerifierDecision;
  verifier_id: string;
  verifier_notes: string;
  dispute_prevented_idr?: number;
  risk_index?: number;
  risk_category?: string;
  primary_driver?: string;
}

export interface AuditActionResponse {
  success: boolean;
  audit_id: string;
  claim_id: string;
  timestamp: string;
  message: string;
}

export interface AuditRecordItem {
  timestamp_utc?: string;
  claim_id_raw?: string;
  claim_pseudo_id?: string;
  verifier_id?: string;
  risk_index?: number;
  risk_category?: string;
  primary_driver?: string;
  ai_recommended_action?: string;
  verifier_decision?: string;
  clinical_notes?: string;
  dispute_prevented_idr?: number;
}

export interface CopilotExplainRequest {
  claim_data: Record<string, unknown>;
  dispute_prevented_idr?: number;
  include_narrative?: boolean;
  include_letter?: boolean;
  gemini_api_key?: string;
}

export interface CopilotExplainResponse {
  claim_id: string;
  narrative?: string | null;
  letter?: string | null;
  dispute_amount_idr: number;
  source: string;
  model: string;
  timestamp: string;
  zero_pii_verified: boolean;
}

export interface ChatMessageItem {
  role: 'user' | 'model';
  text: string;
}

export interface CopilotChatRequest {
  claim_data: Record<string, unknown>;
  prompt: string;
  history?: ChatMessageItem[];
  gemini_api_key?: string;
}

export interface CopilotChatResponse {
  claim_id: string;
  reply: string;
  source: string;
  model: string;
  timestamp: string;
}

export interface CopilotStatusResponse {
  status: string;
  configured: boolean;
  model: string;
  zero_pii: boolean;
}

