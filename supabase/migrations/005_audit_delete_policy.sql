-- Allow users to delete their own audits (only terminal statuses)
CREATE POLICY "Users can delete own completed audits"
    ON public.audits FOR DELETE
    USING (auth.uid() = user_id AND status IN ('complete', 'failed'));
