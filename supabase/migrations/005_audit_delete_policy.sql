-- Allow users to delete their own audits (only non-running ones)
CREATE POLICY "Users can delete own non-running audits"
    ON public.audits FOR DELETE
    USING (auth.uid() = user_id AND status != 'running');
