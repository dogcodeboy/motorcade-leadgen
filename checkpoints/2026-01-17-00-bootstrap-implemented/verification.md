# Verification checklist (pass/fail)

- [ ] `ansible-playbook ... 00-bootstrap.yml` completes without errors
- [ ] `nginx -t` passes
- [ ] `curl -s http://leadgen.motorcade.vip/_nginx_health` returns `ok`
- [ ] `getsebool httpd_can_network_connect` shows `on`
- [ ] Directories exist:
  - [ ] `/opt/motorcade-leadgen`
  - [ ] `/var/lib/motorcade-leadgen`
  - [ ] `/var/log/motorcade-leadgen`
- [ ] `systemctl is-enabled leadgen-api.service` returns `enabled`
- [ ] `systemctl status leadgen-api.service` shows **inactive (dead)** (until image exists)
