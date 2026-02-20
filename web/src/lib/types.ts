export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      audit_anomalies: {
        Row: {
          anomaly_type: string
          audit_id: string
          created_at: string
          description: string
          detected_at_cycle: number
          id: string
          related_postulate_id: string | null
          resolved: boolean
          severity: string
          suggested_queries: Json
        }
        Insert: {
          anomaly_type: string
          audit_id: string
          created_at?: string
          description: string
          detected_at_cycle?: number
          id?: string
          related_postulate_id?: string | null
          resolved?: boolean
          severity: string
          suggested_queries?: Json
        }
        Update: {
          anomaly_type?: string
          audit_id?: string
          created_at?: string
          description?: string
          detected_at_cycle?: number
          id?: string
          related_postulate_id?: string | null
          resolved?: boolean
          severity?: string
          suggested_queries?: Json
        }
        Relationships: [
          {
            foreignKeyName: "audit_anomalies_audit_id_fkey"
            columns: ["audit_id"]
            isOneToOne: false
            referencedRelation: "audits"
            referencedColumns: ["id"]
          },
        ]
      }
      audit_findings: {
        Row: {
          audit_id: string
          citations: Json
          created_at: string
          description: string
          discovered_at_cycle: number
          finding_type: string
          id: string
          language: string
          metadata: Json
          name: string
          source_query: string
        }
        Insert: {
          audit_id: string
          citations?: Json
          created_at?: string
          description?: string
          discovered_at_cycle?: number
          finding_type: string
          id?: string
          language?: string
          metadata?: Json
          name: string
          source_query?: string
        }
        Update: {
          audit_id?: string
          citations?: Json
          created_at?: string
          description?: string
          discovered_at_cycle?: number
          finding_type?: string
          id?: string
          language?: string
          metadata?: Json
          name?: string
          source_query?: string
        }
        Relationships: [
          {
            foreignKeyName: "audit_findings_audit_id_fkey"
            columns: ["audit_id"]
            isOneToOne: false
            referencedRelation: "audits"
            referencedColumns: ["id"]
          },
        ]
      }
      audits: {
        Row: {
          anomalies: Json
          completed_at: string | null
          country: string
          coverage_history: Json
          created_at: string
          current_cycle: number
          discipline: string
          error_message: string | null
          findings: Json
          id: string
          max_cycles: number
          multi_agent_result: Json | null
          postulates: Json
          report_url: string | null
          started_at: string | null
          status: string
          topic: string
          updated_at: string
          user_id: string
        }
        Insert: {
          anomalies?: Json
          completed_at?: string | null
          country: string
          coverage_history?: Json
          created_at?: string
          current_cycle?: number
          discipline: string
          error_message?: string | null
          findings?: Json
          id?: string
          max_cycles?: number
          multi_agent_result?: Json | null
          postulates?: Json
          report_url?: string | null
          started_at?: string | null
          status?: string
          topic: string
          updated_at?: string
          user_id: string
        }
        Update: {
          anomalies?: Json
          completed_at?: string | null
          country?: string
          coverage_history?: Json
          created_at?: string
          current_cycle?: number
          discipline?: string
          error_message?: string | null
          findings?: Json
          id?: string
          max_cycles?: number
          multi_agent_result?: Json | null
          postulates?: Json
          report_url?: string | null
          started_at?: string | null
          status?: string
          topic?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "audits_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          anthropic_key_encrypted: string | null
          audits_this_month: number
          created_at: string
          display_name: string | null
          email: string | null
          id: string
          monthly_reset_at: string
          plan: string
          stripe_customer_id: string | null
          updated_at: string
        }
        Insert: {
          anthropic_key_encrypted?: string | null
          audits_this_month?: number
          created_at?: string
          display_name?: string | null
          email?: string | null
          id: string
          monthly_reset_at?: string
          plan?: string
          stripe_customer_id?: string | null
          updated_at?: string
        }
        Update: {
          anthropic_key_encrypted?: string | null
          audits_this_month?: number
          created_at?: string
          display_name?: string | null
          email?: string | null
          id?: string
          monthly_reset_at?: string
          plan?: string
          stripe_customer_id?: string | null
          updated_at?: string
        }
        Relationships: []
      }
      usage_records: {
        Row: {
          audit_id: string | null
          created_at: string
          event_type: string
          id: string
          metadata: Json
          user_id: string
        }
        Insert: {
          audit_id?: string | null
          created_at?: string
          event_type: string
          id?: string
          metadata?: Json
          user_id: string
        }
        Update: {
          audit_id?: string | null
          created_at?: string
          event_type?: string
          id?: string
          metadata?: Json
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "usage_records_audit_id_fkey"
            columns: ["audit_id"]
            isOneToOne: false
            referencedRelation: "audits"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "usage_records_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      check_audit_limit: { Args: { p_user_id: string }; Returns: boolean }
      reset_monthly_audit_counts: { Args: never; Returns: undefined }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type PublicSchema = Database[Extract<keyof Database, "public">]

export type Tables<
  TableName extends keyof PublicSchema["Tables"]
> = PublicSchema["Tables"][TableName]["Row"]

// --- Application types (convenience aliases) ---

export type Profile = Tables<"profiles">
export type Audit = Tables<"audits">
export type AuditFinding = Tables<"audit_findings">
export type AuditAnomaly = Tables<"audit_anomalies">
export type UsageRecord = Tables<"usage_records">

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
