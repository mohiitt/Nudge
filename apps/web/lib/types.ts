/** TypeScript mirrors of services/agent/app/contracts.py */

export type AccountStatus = "active" | "churn_risk" | "churned" | "expansion";
export type TicketStatus = "open" | "pending" | "solved" | "closed";
export type ApprovalStatus = "pending" | "approved" | "rejected" | "expired";
export type ActionStatus =
  | "proposed"
  | "approved"
  | "rejected"
  | "executed"
  | "failed"
  | "skipped";
export type InterventionOutcome =
  | "pending"
  | "improved"
  | "unchanged"
  | "worsened"
  | "unknown";
export type PreferredChannel = "email" | "call" | "slack" | "linkedin";
export type Priority = "low" | "medium" | "high" | "urgent";

export type SensitiveActionType =
  | "external_email"
  | "discount"
  | "contract_change"
  | "refund"
  | "slack_escalate"
  | "create_task";

export interface CSM {
  csm_id: string;
  email: string;
  full_name: string;
  timezone: string;
}

export interface CSMPreferences {
  csm_id: string;
  preferred_channel: PreferredChannel;
  briefing_hour_local: number;
  risk_threshold: number;
  prefs_json?: Record<string, unknown> | null;
}

export interface Account {
  account_id: string;
  name: string;
  industry?: string | null;
  arr: number;
  plan_tier?: string | null;
  renewal_date?: string | null;
  health_score?: number | null;
  status: AccountStatus;
  owner_csm_id: string;
}

export interface RiskSignal {
  account_id: string;
  owner_csm_id: string;
  name: string;
  arr: number;
  renewal_date?: string | null;
  usage_delta_30d: number;
  open_tickets: number;
  days_to_renewal?: number | null;
  failed_payments: number;
  risk_score: number;
  reasons: string[];
}

export interface TicketChunk {
  chunk_id: string;
  account_id: string;
  owner_csm_id: string;
  ticket_id: string;
  category?: string | null;
  sentiment?: string | null;
  created_at: string;
  text_redacted: string;
  similarity?: number | null;
}

export interface SimilarAccount {
  account_id: string;
  name: string;
  similarity: number;
  intervention_summary?: string | null;
  outcome?: InterventionOutcome | null;
}

export interface Recommendation {
  recommendation_id: string;
  account_id: string;
  owner_csm_id: string;
  title: string;
  rationale: string;
  suggested_actions: string[];
  priority: Priority;
  risk_score?: number | null;
}

export interface BriefingItem {
  account: Account;
  risk: RiskSignal;
  top_reasons: string[];
  recommended_next_step?: string | null;
}

export interface DailyBriefing {
  csm_id: string;
  generated_at: string;
  items: BriefingItem[];
  summary: string;
}

export interface AccountDeepDive {
  account: Account;
  risk: RiskSignal;
  usage_delta_30d: number;
  open_tickets: number;
  recent_tickets: TicketChunk[];
  similar_accounts: SimilarAccount[];
  recommendations: Recommendation[];
  recent_activities: Record<string, unknown>[];
}

export interface ActionRequest {
  action_id: string;
  csm_id: string;
  account_id?: string | null;
  action_type: string;
  tool_name: string;
  title: string;
  description?: string | null;
  payload: Record<string, unknown>;
  requires_approval: boolean;
  status: ActionStatus;
}

export interface Approval {
  approval_id: string;
  csm_id: string;
  account_id?: string | null;
  action_type: string;
  title: string;
  description?: string | null;
  payload: Record<string, unknown>;
  status: ApprovalStatus;
  decided_by?: string | null;
  decided_at?: string | null;
  created_at: string;
  expires_at?: string | null;
}

export interface ApprovalDecision {
  approval_id: string;
  decision: "approved" | "rejected";
  decided_by: string;
  note?: string | null;
}

export interface ChatRequest {
  message: string;
  session?: string | null;
  csm_id?: string | null;
}

export interface ChatResponse {
  reply: string;
  session?: string | null;
  actions: ActionRequest[];
  approvals: Approval[];
}

export interface MockBundle {
  csm: CSM;
  preferences: CSMPreferences;
  briefing: DailyBriefing;
  accounts: Account[];
  approvals: Approval[];
  deepDives: Record<string, AccountDeepDive>;
}
