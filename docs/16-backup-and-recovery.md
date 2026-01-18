# Backup & Recovery (Local-first)

## Phase 1 (now): Local-first backups
- Backups are created locally (filesystem) and verified with manifests + hashes.
- No S3 integration in Phase 1.

## Backup bundle contents
- DB dump (compressed)
- Artifacts/templates snapshot
- Config snapshot (no plaintext secrets)
- Manifest JSON + sha256

## Mini-app (GUI) requirement
Provide a small local tool (desktop mini-app) that:
- lets operator choose backup destination every run
- runs Quick Backup / Full Backup / Verify
- shows progress/logs
- outputs a portable bundle

## Phase 2 (later): Remote recovery expansion
- Add optional UI to select `.pem` and server address for remote backup/restore.
- Keep feature behind a flag; not implemented now.
