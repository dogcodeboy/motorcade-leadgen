# Playbook 00: Bootstrap — intent & behavior

**Purpose:** Prepare a host to run LeadGen containers behind an existing Nginx edge.

## What it installs/configures
- Installs packages: `podman`, `firewalld`, `policycoreutils-python-utils`, etc.
- Creates a non-login system user: `leadgen`
- Creates directories:
  - `/opt/motorcade-leadgen/{config,secrets,containers}`
  - `/var/lib/motorcade-leadgen/{db,uploads}`
  - `/var/log/motorcade-leadgen`
- Sets SELinux boolean: `httpd_can_network_connect=on`
- Writes Nginx vhost for `leadgen.motorcade.vip` proxying to `127.0.0.1:18080` (optional toggle)
- Installs Podman Quadlet unit `/etc/containers/systemd/leadgen-api.container`
  - Placeholder image: `localhost/motorcade-leadgen-api:latest`
  - Service enabled but stopped until playbook 01 builds/pulls the image

## Variables
Defaults are in `ansible/roles/leadgen-host-bootstrap/defaults/main.yml` and can be overridden via group_vars.

## Safety
- Does not touch `/var/www`.
- Does not expose container ports publicly (binds to localhost).
