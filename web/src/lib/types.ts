/* Supabase Database types + shared application types */

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: Profile;
        Insert: Partial<Profile>;
        Update: Partial<Profile>;
      };
      audits: {
        Row: Audit;
        Insert: AuditInsert;
        Update: Partial<Audit>;
      };
      audit_findings: {
        Row: AuditFinding;
        Insert: Omit<AuditFinding, "id" | "created_at">;
        Update: Partial<AuditFinding>;
      };
      audit_anomalies: {
        Row: AuditAnomaly;
        Insert: Omit<AuditAnomaly, "id" | "created_at">;
        Update: Partial<AuditAnomaly>;
      };
      usage_records: {
        Row: UsageRecord;
        Insert: Omit<UsageRecord, "id" | "created_at">;
        Update: Partial<UsageRecord>;
      };
    };
    Functions: {
      check_audit_limit: {
        Args: { p_user_id: string };
        Returns: boolean;
      };
    };
  };
}

// --- Row types ---

export interface Profile {
  id: string;
  email: string | null;
  display_name: string | null;
  plan: "free" | "pro" | "enterprise";
  anthropic_key_encrypted: string | null;
  audits_this_month: number;
  monthly_reset_at: string;
  stripe_customer_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Audit {
  id: string;
  user_id: string;
  topic: string;
  country: string;
  discipline: string;
  max_cycles: number;
  status: "pending" | "running" | "complete" | "failed";
  current_cycle: number;
  error_message: string | null;
  coverage_history: CoveragePoint[];
  findings: FindingData[];
  postulates: PostulateData[];
  anomalies: AnomalyData[];
  multi_agent_result: MultiAgentResult | null;
  report_url: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditInsert {
  user_id: string;
  topic: string;
  country: string;
  discipline: string;
  max_cycles?: number;
}

export interface AuditFinding {
  id: string;
  audit_id: string;
  name: string;
  finding_type: string;
  description: string;
  source_query: string;
  language: string;
  citations: string[];
  metadata: Record<string, unknown>;
  discovered_at_cycle: number;
  created_at: string;
}

export interface AuditAnomaly {
  id: string;
  audit_id: string;
  anomaly_type: string;
  severity: "critical" | "high" | "medium";
  description: string;
  suggested_queries: string[];
  related_postulate_id: string | null;
  detected_at_cycle: number;
  resolved: boolean;
  created_at: string;
}

export interface UsageRecord {
  id: string;
  user_id: string;
  audit_id: string | null;
  event_type: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

// --- JSONB embedded types ---

export interface CoveragePoint {
  cycle: number;
  percentage: number;
  confirmed?: number;
  total?: number;
}

export interface FindingData {
  name: string;
  finding_type: string;
  description: string;
  source_query: string;
  language: string;
  citations: string[];
  metadata: Record<string, unknown>;
}

export interface PostulateData {
  id: string;
  description: string;
  meta_axiom_id: string;
  status: "unconfirmed" | "confirmed" | "refuted";
  confirming_findings: string[];
  generated_at_cycle: number;
}

export interface AnomalyData {
  id: string;
  anomaly_type: string;
  severity: "critical" | "high" | "medium";
  description: string;
  suggested_queries: string[];
  related_postulate_id: string;
  detected_at_cycle: number;
  resolved: boolean;
}

export interface MultiAgentResult {
  alpha: AgentSummary;
  beta: AgentSummary;
  combined: {
    coverage: number;
    blindness_gap: number;
    total_anomalies: number;
    known_unknowns: number;
  };
  agreements: string[];
  discrepancies: string[];
  known_unknowns: {
    type: string;
    severity: string;
    description: string;
  }[];
}

export interface AgentSummary {
  coverage: number;
  findings: number;
  anomalies: number;
  coverage_history: CoveragePoint[];
}
