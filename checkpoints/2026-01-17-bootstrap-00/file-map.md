# File Map

- `ansible/playbooks/00-bootstrap.yml` — host bootstrap playbook
- `ansible/roles/leadgen-host-bootstrap/tasks/main.yml` — packages, users, dirs, SELinux boolean, nginx config
- `ansible/roles/leadgen-host-bootstrap/templates/nginx_leadgen.conf.j2` — vhost for `leadgen.motorcade.vip`
- `ansible/roles/leadgen-host-bootstrap/handlers/main.yml` — nginx reload
- `ansible/roles/leadgen-host-bootstrap/defaults/main.yml` — defaults and tunables
