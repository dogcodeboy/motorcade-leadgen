# Deprecated Playbooks Policy (Canonical)

## Goals
- Preserve provenance while keeping active playbooks clean and predictable.
- Prevent accidental execution of superseded/prohibited/known-broken playbooks.
- Enable a safe purge pass later once references are removed.

## Rules
1. Prefer **DEPRECATE** over delete during active buildout.
2. Deprecate by:
   - Moving to `playbooks/deprecated/` (repo’s canonical deprecated folder), and
   - Adding a header banner:
     - `⚠️ DEPRECATED — DO NOT RUN`
     - Reason
     - Replacement playbook (if any)
     - Checkpoint provenance
3. RUNBOOK must only point to **runnable** playbooks.
4. Maintain `docs/reports/PURGE_CANDIDATES.md` for visibility.

## Purge (later)
Delete only when:
- The playbook has **zero references** across repo text files.
- A replacement is verified and referenced by RUNBOOK.
- The deletion is recorded in a **PURGE checkpoint**.
