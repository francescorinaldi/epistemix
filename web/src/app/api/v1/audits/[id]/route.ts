import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase-server";

/**
 * GET  /api/v1/audits/:id — Get audit status and results
 * POST /api/v1/audits/:id — Stop an audit early (action=stop)
 */

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const supabase = await createServerSupabaseClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { data: audit, error } = await supabase
      .from("audits")
      .select("*")
      .eq("id", id)
      .single();

    if (error || !audit) {
      return NextResponse.json({ error: "Audit not found" }, { status: 404 });
    }

    return NextResponse.json(audit);
  } catch (err) {
    console.error("GET /api/v1/audits/:id error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const supabase = await createServerSupabaseClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();

    if (body.action === "stop") {
      const { error } = await supabase
        .from("audits")
        .update({
          status: "complete",
          completed_at: new Date().toISOString(),
        })
        .eq("id", id)
        .eq("status", "running");

      if (error) {
        return NextResponse.json(
          { error: "Failed to stop audit" },
          { status: 500 }
        );
      }

      return NextResponse.json({ success: true, message: "Audit stopped" });
    }

    return NextResponse.json({ error: "Unknown action" }, { status: 400 });
  } catch (err) {
    console.error("POST /api/v1/audits/:id error:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
