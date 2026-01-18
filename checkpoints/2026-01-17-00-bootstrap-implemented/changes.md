# Changes in this checkpoint

## Added
- `ansible/roles/leadgen-host-bootstrap/`
  - `defaults/main.yml`
  - `tasks/main.yml`
  - `handlers/main.yml`
  - `templates/nginx_leadgen.conf.j2`

## Updated
- `ansible/playbooks/00-bootstrap.yml` (now runs the role)
- `docs/17-bootstrap/README.md` (execution + verification)

## Not changed
- `ansible/vault.yml` remains a placeholder and should be encrypted by the operator.
- Playbooks `01-09` remain placeholders (next checkpoints).
