# PURGE_CANDIDATES — motorcade-leadgen
Generated during cleanup. This does **not** delete anything.

Legend:
- KEEP: referenced/active
- DEPRECATE: move to deprecated/ + banner
- PURGE LATER: delete only after references removed + verified replacement

| Playbook | References | Suggested | Notes |
|---|---:|---|---|
| `00-bootstrap.yml` | 14 | KEEP |  |
| `01-app.yml` | 0 | DEPRECATE | possible duplicate naming; 0 refs |
| `01-leadgen-app.yml` | 6 | KEEP | possible duplicate naming |
| `02-api.yml` | 3 | KEEP |  |
| `02-workers.yml` | 1 | KEEP |  |
| `03-scheduler.yml` | 1 | KEEP |  |
| `04-doc-generator.yml` | 1 | KEEP |  |
| `05-security-hardening.yml` | 2 | KEEP |  |
| `06-monitoring.yml` | 1 | KEEP |  |
| `07-backup.yml` | 3 | KEEP |  |
| `08-restore.yml` | 2 | KEEP |  |
| `09-dr-cutover.yml` | 1 | KEEP |  |
