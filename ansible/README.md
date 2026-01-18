# Motorcade LeadGen Ansible

## Standards (LOCKED)
- **Secrets:** `ansible/vault.yml` (encrypted)
- **Execution:** always run with `--ask-vault-pass`
- **SSH:** key-only (PEM). No password login.

## Playbook order
- `00-bootstrap.yml` — host prereqs + nginx proxy + quadlet units
- `01-leadgen-app.yml` — build/deploy LeadGen API image and start service (next)
- `07-backup.yml` / `08-restore.yml` — local-first backup & recovery

## Example
```bash
ansible-playbook -i ansible/inventory/production.yml ansible/playbooks/00-bootstrap.yml \
  --ask-vault-pass --private-key /path/to/key.pem
```
