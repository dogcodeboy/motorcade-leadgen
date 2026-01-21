# LeadGen API (Lead Intake) — v1

This repo implements the **Lead Intake API** for the Motorcade LeadGen system.

## Authoritative Contract
- See: `docs/19-api/lead-intake-v1.md`

## Endpoints (v1)
- `GET /lead/health` → liveness/readiness (no auth)
- `POST /lead/intake` → validate + accept + enqueue (**202 Accepted**) (requires `X-API-Key`)
- `GET /version` → internal convenience endpoint

## Security posture
- Service port is **internal-only** (do not open 8000 to the internet).
- Use a reverse proxy later (infra playbook PLAT_06) to expose only 443.
- Secrets are injected from `vault.yml` into `{{ leadgen_install_root }}/secrets/leadgen.env` (mode `0600`).

## Required secrets (env)
- `LEADGEN_API_KEY` (shared secret used for `X-API-Key`)

## Idempotency
- Optional header: `Idempotency-Key`
- Same key + same payload returns the same `intake_id`
- Same key + different payload returns **409**

## Run (when you are ready)
From `motorcade-leadgen/ansible`:

```bash
ansible-playbook -i inventory/production.yml playbooks/02-api.yml --ask-vault-pass
```

> Note: deployment/testing is not active yet; this doc and the contract are being locked before infra wiring.
