# Next implementation step

**Playbook 01 — LeadGen App** (next checkpoint):

- Decide image build workflow (Podman build on host vs CI push/pull)
- Implement:
  - container image deployment for `localhost/motorcade-leadgen-api:latest`
  - secrets injection from `ansible/vault.yml` into `/opt/motorcade-leadgen/secrets`
  - systemd start of `leadgen-api.service`
  - basic `/health` endpoint contract (even before full API)

Secondary (after 01): worker containers (02), scheduler (03), doc generator (04).
