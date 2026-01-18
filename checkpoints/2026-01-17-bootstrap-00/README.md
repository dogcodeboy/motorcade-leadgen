# Checkpoint: 2026-01-17-bootstrap-00

This checkpoint implements the **first executable playbook** for the Motorcade LeadGen system.

## What shipped
- Implemented `ansible/playbooks/00-bootstrap.yml` (real playbook, no longer placeholder)
- Added new Ansible role: `ansible/roles/leadgen-host-bootstrap`
- Installs host prerequisites, creates LeadGen directories, and installs Nginx reverse proxy config for `leadgen.motorcade.vip`
- Enables SELinux boolean: `httpd_can_network_connect`

## What did NOT ship
- No application code
- No containers deployed
- No DB
- No TLS/Certbot automation (intentionally deferred to hardening playbook)

## Next
Implement `01-leadgen-app.yml` to deploy the container stack (API + workers + doc generator) and wire systemd/quadlet.
