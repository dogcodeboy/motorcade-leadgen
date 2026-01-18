```bash
cd motorcade-leadgen/ansible
ansible-playbook -i inventory/production.yml playbooks/02-api.yml --ask-vault-pass

# verify locally on host
curl -fsS http://127.0.0.1:18080/health
curl -fsS http://127.0.0.1:18080/version
```
