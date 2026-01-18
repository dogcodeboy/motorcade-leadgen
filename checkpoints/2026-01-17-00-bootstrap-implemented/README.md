# Checkpoint: 2026-01-17 — 00-bootstrap implemented

This checkpoint implements the first executable Ansible playbook for the Motorcade LeadGen system: **00-bootstrap**.

Scope: **host prerequisites only** (Podman runtime, directories, nginx reverse proxy, SELinux boolean, quadlet stub). No application code is deployed.

## Repo state
- Repo: `motorcade-leadgen/`
- Key deliverables:
  - `ansible/playbooks/00-bootstrap.yml`
  - `ansible/roles/leadgen-host-bootstrap/`
  - Updated doc: `docs/17-bootstrap/README.md`

## Canonical constraints re-confirmed
- LeadGen runs containerized, behind host Nginx (LEMP edge).
- No filesystem overlap with `/var/www`.
- SELinux respected.
- Secrets remain in `ansible/vault.yml`; playbooks run with `--ask-vault-pass`.
- SSH is PEM key only (inventory shows `ansible_ssh_private_key_file` comment).
