# Rollback notes

This checkpoint is low-risk and easy to revert.

## What to remove if rolling back manually

- Nginx vhost:
  - `/etc/nginx/conf.d/leadgen.motorcade.vip.conf`

- Quadlet:
  - `/etc/containers/systemd/leadgen-api.container`
  - `systemctl disable --now leadgen-api.service`

- SELinux boolean:
  - `setsebool -P httpd_can_network_connect off`

- Directories:
  - `/opt/motorcade-leadgen`
  - `/var/lib/motorcade-leadgen`
  - `/var/log/motorcade-leadgen`

## Git rollback
Revert commit produced for this checkpoint.
