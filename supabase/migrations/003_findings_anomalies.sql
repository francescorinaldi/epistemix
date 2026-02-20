-- Detailed findings and anomalies as separate tables
-- for efficient querying and filtering

CREATE TABLE public.audit_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL REFERENCES public.audits(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    finding_type TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    source_query TEXT NOT NULL DEFAULT '',
    language TEXT NOT NULL DEFAULT 'en',
    citations JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    discovered_at_cycle INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_findings_audit_id ON public.audit_findings(audit_id);
CREATE INDEX idx_audit_findings_type ON public.audit_findings(finding_type);

-- RLS via audit ownership
ALTER TABLE public.audit_findings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view findings for own audits"
    ON public.audit_findings FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.audits
            WHERE audits.id = audit_findings.audit_id
            AND audits.user_id = auth.uid()
        )
    );


CREATE TABLE public.audit_anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL REFERENCES public.audits(id) ON DELETE CASCADE,
    anomaly_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium')),
    description TEXT NOT NULL,
    suggested_queries JSONB NOT NULL DEFAULT '[]'::jsonb,
    related_postulate_id TEXT,
    detected_at_cycle INT NOT NULL DEFAULT 0,
    resolved BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_anomalies_audit_id ON public.audit_anomalies(audit_id);
CREATE INDEX idx_audit_anomalies_severity ON public.audit_anomalies(severity);

ALTER TABLE public.audit_anomalies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view anomalies for own audits"
    ON public.audit_anomalies FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.audits
            WHERE audits.id = audit_anomalies.audit_id
            AND audits.user_id = auth.uid()
        )
    );
