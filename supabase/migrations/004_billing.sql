-- Usage tracking for billing

CREATE TABLE public.usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    audit_id UUID REFERENCES public.audits(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('audit_started', 'audit_completed', 'cycle_completed')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_usage_records_user_id ON public.usage_records(user_id);
CREATE INDEX idx_usage_records_created_at ON public.usage_records(created_at DESC);

ALTER TABLE public.usage_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own usage"
    ON public.usage_records FOR SELECT
    USING (auth.uid() = user_id);

-- Monthly audit count reset function
-- Called by pg_cron or Supabase scheduled function
CREATE OR REPLACE FUNCTION public.reset_monthly_audit_counts()
RETURNS void AS $$
BEGIN
    UPDATE public.profiles
    SET audits_this_month = 0,
        monthly_reset_at = date_trunc('month', now()) + INTERVAL '1 month'
    WHERE monthly_reset_at <= now();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Plan limits check function
CREATE OR REPLACE FUNCTION public.check_audit_limit(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_plan TEXT;
    v_count INT;
BEGIN
    SELECT plan, audits_this_month
    INTO v_plan, v_count
    FROM public.profiles
    WHERE id = p_user_id;

    CASE v_plan
        WHEN 'free' THEN RETURN v_count <= 3;  -- count already incremented by insert trigger
        WHEN 'pro' THEN RETURN TRUE;  -- unlimited
        WHEN 'enterprise' THEN RETURN TRUE;  -- unlimited
        ELSE RETURN FALSE;
    END CASE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Increment audit count on new audit
CREATE OR REPLACE FUNCTION public.increment_audit_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.profiles
    SET audits_this_month = audits_this_month + 1
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_audit_increment_count
    AFTER INSERT ON public.audits
    FOR EACH ROW EXECUTE FUNCTION public.increment_audit_count();
