export type RiskBand = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

export type AssessmentStatus = "IN_PROGRESS" | "COMPLETE" | "PARTIAL" | "INSUFFICIENT_EVIDENCE";

export type ChannelEnum = "VOICE_CALL" | "WEB_AUDIO" | "CHAT_TEXT" | "WHATSAPP" | "WALK_IN";

export type SessionStatusEnum = "INITIALIZED" | "ACTIVE" | "COMPLETED" | "ABANDONED";

export type ConsentType = "AUDIO_RECORDING" | "AI_ASSESSMENT" | "DATA_RETENTION";

export type ConsentStatus = "GRANTED" | "DENIED" | "REVOKED";

export type CaseStatus = "OPEN" | "IN_REVIEW" | "ESCALATED" | "RESOLVED" | "CLOSED";

export interface SessionResponse {
  id: string;
  channel: ChannelEnum;
  status: SessionStatusEnum;
  language: string;
  created_at: string;
  closed_at?: string | null;
}

export interface ConsentRecord {
  id: string;
  session_id: string;
  consent_type: ConsentType;
  status: ConsentStatus;
  granted_at: string;
  notes?: string | null;
}

export interface CaseResponse {
  id: string;
  session_id: string;
  status: CaseStatus;
  priority: RiskBand;
  assigned_to?: string | null;
  initial_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface HumanReviewCreate {
  reviewer_id: string;
  final_action: "CONFIRM" | "ESCALATE" | "DOWNGRADE" | "CLOSE";
  modified_priority?: RiskBand;
  reason?: string;
}

export interface HumanReviewResponse {
  id: string;
  case_id: string;
  reviewer_id: string;
  final_action: string;
  modified_priority?: RiskBand;
  reason?: string;
  created_at: string;
}

export interface MasterAssessmentObject {
  session_id: string;
  case_id?: string | null;
  assessment_status: AssessmentStatus;
  svi: number;
  risk_band: RiskBand;
  confidence: number;
  evidence_coverage: number;
  safety_override: boolean;
  modality_scores: {
    voice?: number;
    text?: number;
    self_report?: number;
    context?: number;
    interaction?: number;
  };
  quality: {
    voice?: number;
    text?: number;
    self_report?: number;
    context?: number;
    interaction?: number;
  };
  contributions: {
    voice?: number;
    text?: number;
    self_report?: number;
    context?: number;
    interaction?: number;
  };
  contributors: string[];
  missing_evidence: string[];
  support_recommendations: string[];
}
