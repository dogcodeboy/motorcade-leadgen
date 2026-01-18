# Motorcade LeadGen (Scaffold)

This repository is the design-first scaffold for Motorcade's location-based lead generation, assessment, and proposal/contract generation system.

## High-level architecture
- **motorcade.vip (WordPress)** remains the public trust site and lightweight intake.
- **LeadGen** runs as an independent service (recommended: `leadgen.motorcade.vip`) providing:
  - lead intelligence + tracking
  - assessment workflows
  - doctrine-enforced pricing/assets/staffing outputs
  - proposal + addendum generation
  - audit logging

## Current status
- **Design/spec phase only** (no implementation code yet).
- Docs in `docs/` are canonical; changes must be made via docs + checkpoints.

## Operator notes
- Prefer Ansible for deployment automation.
- Secrets live in `ansible/vault.yml` (encrypted); run playbooks with `--ask-vault-pass`.
- Server access is via `.pem` key (SSH key-based auth).

## Next steps
See `checkpoints/2026-01-leadgen-design/next-steps.md`.
