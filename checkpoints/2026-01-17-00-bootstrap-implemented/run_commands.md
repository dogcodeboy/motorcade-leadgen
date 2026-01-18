# Run commands

From `motorcade-leadgen/ansible`:

```bash
ansible-playbook -i inventory/production.yml playbooks/00-bootstrap.yml --ask-vault-pass
```

## Suggested verify steps

```bash
nginx -t
systemctl status nginx
curl -s http://leadgen.motorcade.vip/_nginx_health
systemctl is-enabled leadgen-api.service
systemctl status leadgen-api.service
```

Expected: `leadgen-api.service` enabled but **stopped** until playbook 01.
