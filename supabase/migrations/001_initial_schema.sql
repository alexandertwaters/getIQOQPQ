-- getIQOQPQ initial schema for Supabase
-- Run via: supabase db push (or apply via Supabase dashboard)

-- Enable UUID extension if not already
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- packages: metadata for generated IQ/OQ/PQ advisory packages
CREATE TABLE IF NOT EXISTS packages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fingerprint TEXT UNIQUE NOT NULL,
  package_json JSONB NOT NULL,
  artifact_path TEXT,
  ruleset_id TEXT,
  hazcat_version TEXT,
  qualification_band TEXT,
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for lookups by fingerprint and user
CREATE INDEX IF NOT EXISTS idx_packages_fingerprint ON packages(fingerprint);
CREATE INDEX IF NOT EXISTS idx_packages_created_by ON packages(created_by);
CREATE INDEX IF NOT EXISTS idx_packages_created_at ON packages(created_at DESC);

-- generation_events: audit trail for usage/billing (userId, equipment type, fingerprint, rulesetId, hazcatVersion)
CREATE TABLE IF NOT EXISTS generation_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  equipment_type TEXT,
  fingerprint TEXT NOT NULL,
  ruleset_id TEXT,
  hazcat_version TEXT,
  residual_risk_index NUMERIC,
  qualification_band TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_generation_events_user_id ON generation_events(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_events_created_at ON generation_events(created_at DESC);

-- RLS policies: allow authenticated users to read their own packages
ALTER TABLE packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own packages"
  ON packages FOR SELECT
  USING (auth.uid() = created_by OR created_by IS NULL);

CREATE POLICY "Service role can manage packages"
  ON packages FOR ALL
  USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Users can read own generation events"
  ON generation_events FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert generation events"
  ON generation_events FOR INSERT
  WITH CHECK (true);

-- Storage: create artifacts bucket (run via Supabase dashboard or API)
-- Bucket name: artifacts
-- Public: false (use signed URLs via API)
