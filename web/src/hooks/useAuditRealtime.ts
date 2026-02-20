"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase";
import type { Audit } from "@/lib/types";

/**
 * Subscribe to real-time updates for a specific audit.
 * Uses Supabase Realtime to receive row-level changes
 * as the worker updates coverage, findings, anomalies.
 */
export function useAuditRealtime(auditId: string) {
  const [audit, setAudit] = useState<Audit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  useEffect(() => {
    // Initial fetch
    async function fetchAudit() {
      const { data, error } = await supabase
        .from("audits")
        .select("*")
        .eq("id", auditId)
        .single();

      if (error) {
        setError(error.message);
      } else {
        setAudit(data);
      }
      setLoading(false);
    }

    fetchAudit();

    // Subscribe to changes
    const channel = supabase
      .channel(`audit-${auditId}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "audits",
          filter: `id=eq.${auditId}`,
        },
        (payload) => {
          setAudit(payload.new as Audit);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [auditId]);

  return { audit, loading, error };
}
