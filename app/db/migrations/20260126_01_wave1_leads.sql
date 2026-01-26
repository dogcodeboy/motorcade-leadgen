-- LeadGen Wave 1 — durable intake persistence (schema: app)
-- Migration: 20260126_01_wave1_leads
-- Idempotent: safe to re-run.

BEGIN;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Migration ledger (tiny, explicit)
CREATE TABLE IF NOT EXISTS app.schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Lead record (Wave 1)
-- NOTE: WordPress remains non-authoritative. This table is the durable store.
CREATE TABLE IF NOT EXISTS app.leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Contact
  full_name TEXT NOT NULL,
  company TEXT NULL,
  email TEXT NULL,
  phone TEXT NULL,
  preferred_contact_method TEXT NULL,

  -- Request payload (Wave 1 keeps the raw request JSON for forward compatibility)
  service_type TEXT NULL,
  timeline_start_local TEXT NULL,
  timeline_end_local TEXT NULL,
  location_street TEXT NULL,
  location_city TEXT NULL,
  location_state TEXT NULL,
  location_postal_code TEXT NULL,
  site_type TEXT NULL,
  notes TEXT NULL,
  expected_hours INTEGER NULL,
  recurrence TEXT NULL,

  -- Context
  lead_source TEXT NOT NULL DEFAULT 'unknown',
  referrer_url TEXT NULL,
  utm_source TEXT NULL,
  utm_medium TEXT NULL,
  utm_campaign TEXT NULL,

  -- Progressive consent state:
  -- local_only: frontend-only autosave; never persisted server-side
  -- server_draft: persisted only after email/phone shown + inline notice
  -- opted_in: explicit opt-in for SMS/scheduling (future); Wave 1 records but does not act
  consent_state TEXT NOT NULL DEFAULT 'server_draft',

  -- Privacy: store hashed IP only (never raw IP)
  ip_hash TEXT NULL,

  -- Idempotency / tracing
  idempotency_key TEXT NULL,
  request_id TEXT NULL
);

-- Constraints
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'leads_consent_state_ck'
      AND conrelid = 'app.leads'::regclass
  ) THEN
    ALTER TABLE app.leads
      ADD CONSTRAINT leads_consent_state_ck
      CHECK (consent_state IN ('local_only', 'server_draft', 'opted_in'));
  END IF;
END $$;

-- Indexes
CREATE INDEX IF NOT EXISTS leads_created_at_idx ON app.leads (created_at DESC);
CREATE INDEX IF NOT EXISTS leads_email_idx ON app.leads (email);
CREATE INDEX IF NOT EXISTS leads_phone_idx ON app.leads (phone);
CREATE INDEX IF NOT EXISTS leads_consent_state_idx ON app.leads (consent_state);
CREATE UNIQUE INDEX IF NOT EXISTS leads_idempotency_key_uidx
  ON app.leads (idempotency_key)
  WHERE idempotency_key IS NOT NULL;

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION app.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_leads_set_updated_at ON app.leads;
CREATE TRIGGER trg_leads_set_updated_at
BEFORE UPDATE ON app.leads
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();

-- Record migration
INSERT INTO app.schema_migrations (version)
VALUES ('20260126_01_wave1_leads')
ON CONFLICT (version) DO NOTHING;

COMMIT;
