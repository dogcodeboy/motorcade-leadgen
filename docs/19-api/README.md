# Playbook 02 — LeadGen API Container (Build + Deploy)

This checkpoint introduces the **first running component** of the LeadGen system: a minimal API container.

## Endpoints
- `GET /health` → `{ "status": "ok" }`
- `GET /version` → `{ service, version, env }`

## Security posture
- Secrets are injected from `vault.yml` into `{{ leadgen_install_root }}/secrets/leadgen.env` (mode `0600`).
- Quadlet mounts secrets read-only path and uses `EnvironmentFile=/run/secrets/leadgen.env`.
- Container drops all Linux capabilities and sets `NoNewPrivileges=true`.

## Run
From `motorcade-leadgen/ansible`:

```bash
ansible-playbook -i inventory/production.yml playbooks/02-api.yml --ask-vault-pass
```

## Vault requirement
Add to `ansible/vault.yml`:

```yaml
leadgen_secret_key: "<32+ chars random>"
```
