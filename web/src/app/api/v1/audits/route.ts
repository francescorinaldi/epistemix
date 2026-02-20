import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase-server";
import { maxCyclesForPlan, type PlanName } from "@/lib/stripe";

/**
 * POST /api/v1/audits — Start a new epistemic audit
 * GET  /api/v1/audits — List user's audits
 */

export async function POST(request: NextRequest) {
  try {
    const supabase = await createServerSupabaseClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { topic, country, discipline, max_cycles } = body;

    if (!topic || !country || !discipline) {
      return NextResponse.json(
        { error: "topic, country, and discipline are required" },
        { status: 400 }
      );
    }

    // Get user's plan and check limits
    const { data: profile } = await supabase
      .from("profiles")
      .select("plan, audits_this_month")
      .eq("id", user.id)
      .single();

    if (!profile) {
      return NextResponse.json({ error: "Profile not found" }, { status: 404 });
    }

    const plan = profile.plan as PlanName;
    const planMaxCycles = maxCyclesForPlan(plan);

    // Insert audit row — the database trigger handles:
    // 1. Incrementing audits_this_month
    // 2. Notifying the edge function to start the worker
    const { data: audit, error } = await supabase
      .from("audits")
      .insert({
        user_id: user.id,
        topic: topic.trim(),
        country: country.trim(),
        discipline: discipline.trim(),
        max_cycles: Math.min(max_cycles ?? 4, planMaxCycles),
      })
      .select("id")
      .single();

    if (error) {
      console.error("Audit creation error:", error);
      return NextResponse.json(
        { error: "Failed to create audit" },
        { status: 500 }
      );
    }

    return NextResponse.json({ id: audit.id }, { status: 201 });
  } catch (err) {
    console.error("POST /api/v1/audits error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const supabase = await createServerSupabaseClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { data: audits, error } = await supabase
      .from("audits")
      .select(
        "id, topic, country, discipline, status, current_cycle, coverage_history, created_at"
      )
      .order("created_at", { ascending: false });

    if (error) {
      return NextResponse.json(
        { error: "Failed to fetch audits" },
        { status: 500 }
      );
    }

    return NextResponse.json({ audits });
  } catch (err) {
    console.error("GET /api/v1/audits error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
