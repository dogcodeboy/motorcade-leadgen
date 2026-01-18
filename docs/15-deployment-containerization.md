# Deployment & Containerization (Design)

Local-first, containerized services running behind host Nginx on the existing server.

## Non-conflict constraints
- Host Nginx owns ports 80/443.
- LeadGen containers bind only to localhost high ports (e.g., 8085/8086).
- No writes into `/var/www` or WordPress directories.

## Recommended runtime
- Podman on RHEL/Amazon Linux (Docker-compatible workflow).

## Paths
- /opt/motorcade-leadgen  (compose/units/config)
- /var/lib/motorcade-leadgen (data volumes)
- /var/log/motorcade-leadgen (logs)

## SELinux
Deployment roles must set proper SELinux labels for mounted volumes.

## Resource protection
- Run workers separately from API.
- Set CPU/memory caps on worker containers.

## Recovery Kit
See `docs/16-backup-and-recovery.md`.
