-- Audits: one row per epistemic audit — the single source of truth
-- Status transitions: pending → running → complete | failed

CREATE TABLE public.audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,

    -- Audit configuration
    topic TEXT NOT NULL,
    country TEXT NOT NULL,
    discipline TEXT NOT NULL,
    max_cycles INT NOT NULL DEFAULT 4 CHECK (max_cycles BETWEEN 1 AND 10),

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'complete', 'failed')),
    current_cycle INT NOT NULL DEFAULT 0,
    error_message TEXT,

    -- Results (updated in real-time by the worker)
    coverage_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    findings JSONB NOT NULL DEFAULT '[]'::jsonb,
    postulates JSONB NOT NULL DEFAULT '[]'::jsonb,
    anomalies JSONB NOT NULL DEFAULT '[]'::jsonb,
    multi_agent_result JSONB,

    -- Report
    report_url TEXT,  -- R2/S3 link to PDF/JSON export

    -- Timestamps
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_audits_user_id ON public.audits(user_id);
CREATE INDEX idx_audits_status ON public.audits(status);
CREATE INDEX idx_audits_created_at ON public.audits(created_at DESC);

-- RLS: users only see their own audits
ALTER TABLE public.audits ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own audits"
    ON public.audits FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create audits"
    ON public.audits FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Workers update audits via service role (bypasses RLS)
-- Users can only stop their own running audits (status → complete)
CREATE POLICY "Users can stop own running audits"
    ON public.audits FOR UPDATE
    USING (auth.uid() = user_id AND status = 'running')
    WITH CHECK (auth.uid() = user_id AND status = 'complete');

-- Auto-update updated_at
CREATE TRIGGER audits_updated_at
    BEFORE UPDATE ON public.audits
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- Enable Realtime for live progress updates to the frontend
ALTER PUBLICATION supabase_realtime ADD TABLE public.audits;

-- Notify function for new audits (used by edge function trigger)
CREATE OR REPLACE FUNCTION public.notify_new_audit()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('new_audit', json_build_object(
        'audit_id', NEW.id,
        'user_id', NEW.user_id,
        'topic', NEW.topic,
        'country', NEW.country,
        'discipline', NEW.discipline,
        'max_cycles', NEW.max_cycles
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_audit_created
    AFTER INSERT ON public.audits
    FOR EACH ROW EXECUTE FUNCTION public.notify_new_audit();
