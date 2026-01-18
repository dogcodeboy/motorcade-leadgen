# Next Steps (Implementation Sequencing)

P0 (next): `01-leadgen-app.yml`
- Define container images + runtime (Podman quadlet recommended)
- Bind API to `127.0.0.1:18080` and health to `127.0.0.1:18081`
- Create systemd units and ensure restart on boot
- Render secrets into an env file from `vault.yml`

P1: `07-backup.yml`
- Wire the existing `recovery/backup/*.sh` into host-runner wrapper
- Ensure backups are portable bundles (local-first)

P2: API contracts + templates
- Define request/assessment schema
- Implement proposal render pipeline (40+ pages)
