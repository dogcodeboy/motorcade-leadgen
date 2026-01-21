# Build & Run — Lead Intake API (Local)

This repo defines how to build the LeadGen **Lead Intake API** container image.

## Build (Podman)

From repo root:

```bash
podman build -t motorcade/leadgen:dev -f Containerfile .
```

## Run (Local test)

Create a small env file (do **not** commit it):

```bash
cat > dev.env <<'EOF'
LEADGEN_API_KEY=change-me
LEADGEN_ENV=local
EOF
```

Run:

```bash
podman run --rm -p 8000:8000 --env-file ./dev.env motorcade/leadgen:dev
```

Test:

```bash
curl http://localhost:8000/lead/health
```

## Notes

- Port `8000` is for **internal service** traffic. Do **not** open it publicly in AWS.
- Production secrets are injected by `motorcade-infra` via Ansible vault and mounted env files (e.g., `/run/secrets/leadgen.env`).
- Queue integration is **queue-first**; current enqueue behavior may be stubbed until PLAT_04 wires a real queue.
