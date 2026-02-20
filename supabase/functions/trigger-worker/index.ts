/**
 * Supabase Edge Function: trigger-worker
 *
 * Called via database webhook when a new audit row is inserted.
 * Starts a Fly.io Machine to process the audit, then returns.
 * The machine runs the Python worker, writes results back to Supabase,
 * and shuts down automatically (scale-to-zero).
 */

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const FLY_API_TOKEN = Deno.env.get("FLY_API_TOKEN")!;
const FLY_APP_NAME = Deno.env.get("FLY_APP_NAME") || "epistemix-worker";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const BYOK_ENCRYPTION_KEY = Deno.env.get("BYOK_ENCRYPTION_KEY")!;

interface AuditPayload {
  type: "INSERT";
  table: string;
  record: {
    id: string;
    user_id: string;
    topic: string;
    country: string;
    discipline: string;
    max_cycles: number;
  };
}

/**
 * Decrypt a BYOK API key using AES-GCM.
 * The encrypted value is stored as base64(iv + ciphertext).
 */
async function decryptApiKey(encrypted: string): Promise<string> {
  const rawKey = Uint8Array.from(atob(BYOK_ENCRYPTION_KEY), (c) =>
    c.charCodeAt(0)
  );
  const key = await crypto.subtle.importKey(
    "raw",
    rawKey,
    { name: "AES-GCM" },
    false,
    ["decrypt"]
  );

  const data = Uint8Array.from(atob(encrypted), (c) => c.charCodeAt(0));
  const iv = data.slice(0, 12);
  const ciphertext = data.slice(12);

  const decrypted = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv },
    key,
    ciphertext
  );

  return new TextDecoder().decode(decrypted);
}

serve(async (req: Request) => {
  try {
    const payload: AuditPayload = await req.json();
    const audit = payload.record;

    if (!audit?.id) {
      return new Response(JSON.stringify({ error: "Missing audit ID" }), {
        status: 400,
      });
    }

    // Get user's API key (if BYOK)
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
    const { data: profile } = await supabase
      .from("profiles")
      .select("anthropic_key_encrypted, plan")
      .eq("id", audit.user_id)
      .single();

    // Check plan limits
    const { data: canRun } = await supabase.rpc("check_audit_limit", {
      p_user_id: audit.user_id,
    });

    if (!canRun) {
      await supabase
        .from("audits")
        .update({
          status: "failed",
          error_message: "Monthly audit limit reached. Upgrade your plan.",
        })
        .eq("id", audit.id);

      return new Response(JSON.stringify({ error: "Limit reached" }), {
        status: 429,
      });
    }

    // Update audit status to running
    await supabase
      .from("audits")
      .update({ status: "running", started_at: new Date().toISOString() })
      .eq("id", audit.id);

    // Record usage
    await supabase.from("usage_records").insert({
      user_id: audit.user_id,
      audit_id: audit.id,
      event_type: "audit_started",
    });

    // Decrypt BYOK API key if present
    let decryptedApiKey: string | null = null;
    if (profile?.anthropic_key_encrypted) {
      try {
        decryptedApiKey = await decryptApiKey(profile.anthropic_key_encrypted);
      } catch (err) {
        console.error("Failed to decrypt BYOK key:", err);
      }
    }

    // Start Fly.io Machine
    const machineConfig = {
      config: {
        image: `registry.fly.io/${FLY_APP_NAME}:latest`,
        env: {
          AUDIT_ID: audit.id,
          AUDIT_TOPIC: audit.topic,
          AUDIT_COUNTRY: audit.country,
          AUDIT_DISCIPLINE: audit.discipline,
          AUDIT_MAX_CYCLES: String(audit.max_cycles),
          SUPABASE_URL: SUPABASE_URL,
          SUPABASE_SERVICE_ROLE_KEY: SUPABASE_SERVICE_ROLE_KEY,
          // Pass user's decrypted API key if they have one (BYOK)
          ...(decryptedApiKey ? { ANTHROPIC_API_KEY: decryptedApiKey } : {}),
        },
        auto_destroy: true, // Machine destroyed when process exits
        restart: { policy: "no" }, // Don't restart — one-shot job
        guest: {
          cpu_kind: "shared",
          cpus: 1,
          memory_mb: 512,
        },
      },
    };

    const flyResponse = await fetch(
      `https://api.machines.dev/v1/apps/${FLY_APP_NAME}/machines`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${FLY_API_TOKEN}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(machineConfig),
      }
    );

    if (!flyResponse.ok) {
      const error = await flyResponse.text();
      console.error("Fly.io error:", error);

      await supabase
        .from("audits")
        .update({
          status: "failed",
          error_message: `Worker failed to start: ${flyResponse.status}`,
        })
        .eq("id", audit.id);

      return new Response(JSON.stringify({ error: "Worker start failed" }), {
        status: 502,
      });
    }

    const machine = await flyResponse.json();

    return new Response(
      JSON.stringify({
        success: true,
        audit_id: audit.id,
        machine_id: machine.id,
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (err) {
    console.error("Edge function error:", err);
    return new Response(JSON.stringify({ error: String(err) }), {
      status: 500,
    });
  }
});
