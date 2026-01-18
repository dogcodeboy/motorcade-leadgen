# Run Commands

From `motorcade-leadgen/ansible`:

```bash
ansible-playbook -i inventory/production.yml playbooks/00-bootstrap.yml --ask-vault-pass \
  --private-key /path/to/your.pem
```

## Expected outcomes
- Packages installed (podman, firewalld, policycoreutils-python-utils, etc.)
- Directories created:
  - `/opt/motorcade-leadgen/*`
  - `/var/lib/motorcade-leadgen/*`
  - `/var/log/motorcade-leadgen/*`
- Nginx vhost created:
  - `/etc/nginx/conf.d/leadgen.motorcade.vip.conf`
- SELinux boolean set:
  - `httpd_can_network_connect=on`
