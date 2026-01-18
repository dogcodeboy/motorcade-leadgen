# leadgen-host-bootstrap

Purpose: prepare the host to run Motorcade LeadGen container stack behind Nginx, with SELinux respected.

Includes:
- Podman + base utilities
- LeadGen service directories (no `/var/www` overlap)
- Nginx reverse proxy vhost for `leadgen.motorcade.vip` → `127.0.0.1:18080`
- SELinux boolean to allow Nginx proxying to local upstream

Does **not** deploy containers yet (that starts in `01-leadgen-app.yml`).
