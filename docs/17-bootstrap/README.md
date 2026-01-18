# 17 - Bootstrap (Host Prereqs)

This phase prepares the LeadGen host to run the LeadGen stack as **containers**, behind the existing host Nginx (LEMP edge).

## What this step does

- Installs Podman + required host tooling
- Ensures firewalld is running
- Creates LeadGen-owned directories (no overlap with `/var/www`):
  - `/opt/motorcade-leadgen`
  - `/var/lib/motorcade-leadgen`
  - `/var/log/motorcade-leadgen`
- Sets SELinux boolean `httpd_can_network_connect=on` (so Nginx can proxy to localhost)
- (Optional) Writes an Nginx vhost for `leadgen.motorcade.vip` that proxies to `127.0.0.1:18080`
- Installs a **Quadlet** unit for `leadgen-api`:
  - `leadgen-api.service` is **enabled** but kept **stopped** until the image exists
  - image placeholder: `localhost/motorcade-leadgen-api:latest`

## What this step does NOT do

- Does **not** deploy application code
- Does **not** inject secrets (reserved for playbook `01-leadgen-app.yml`)
- Does **not** bind containers to 80/443 (Nginx retains edge ownership)

## Run

From `motorcade-leadgen/ansible`:

```bash
ansible-playbook -i inventory/production.yml playbooks/00-bootstrap.yml --ask-vault-pass
```

## Verify

- `nginx -t` passes and nginx is running
- `curl -s http://leadgen.motorcade.vip/_nginx_health` returns `ok`
- `systemctl is-enabled leadgen-api.service` returns `enabled` (but it should remain stopped until playbook 01)
