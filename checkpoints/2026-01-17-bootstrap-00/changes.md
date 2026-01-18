# Changes

## Added
- `ansible/roles/leadgen-host-bootstrap/` (tasks, handlers, templates)
- `ansible/roles/leadgen-host-bootstrap/templates/nginx_leadgen.conf.j2`

## Modified
- `ansible/playbooks/00-bootstrap.yml` from placeholder → working bootstrap playbook

## Notes
- Nginx vhost is HTTP-only for bootstrap. HTTPS should be enforced in `05-security-hardening.yml`.
