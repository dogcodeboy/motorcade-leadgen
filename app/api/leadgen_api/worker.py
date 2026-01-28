import json
import os
import signal
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dotenv import load_dotenv

import psycopg
from psycopg.rows import dict_row

from .main import _build_dsn, _insert_lead


# Quadlet mounts /run/secrets and points EnvironmentFile=/run/secrets/leadgen.env
load_dotenv("/run/secrets/leadgen.env", override=False)


SERVICE_NAME = os.getenv("LEADGEN_WORKER_SERVICE_NAME", "lead-intake-worker")
POLL_SECONDS = float(os.getenv("LEADGEN_WORKER_POLL_SECONDS", "0.5"))
MAX_ATTEMPTS = int(os.getenv("LEADGEN_WORKER_MAX_ATTEMPTS", "10"))


_STOP = False


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _handle_stop(_signum, _frame) -> None:
    global _STOP
    _STOP = True


def _log(event: str, **fields: Any) -> None:
    base = {
        "event": event,
        "service": SERVICE_NAME,
        "time_utc": _now_utc_iso(),
    }
    base.update(fields)
    print(json.dumps(base, separators=(",", ":"), sort_keys=True))


def _fetch_one_job(conn: psycopg.Connection) -> Optional[Dict[str, Any]]:
    """Fetch a single queued job and mark it processing.

    Uses SELECT ... FOR UPDATE SKIP LOCKED to allow safe concurrency if we ever
    run >1 worker.
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, idempotency_key, payload, status, attempt_count
            FROM app.intake_jobs
            WHERE status = 'queued'
            ORDER BY created_at ASC
            FOR UPDATE SKIP LOCKED
            LIMIT 1;
            """
        )
        row = cur.fetchone()
        if row is None:
            return None

        cur.execute(
            """
            UPDATE app.intake_jobs
            SET status='processing', attempt_count = attempt_count + 1, updated_at = NOW()
            WHERE id = %s;
            """,
            (row["id"],),
        )
    conn.commit()
    return dict(row)


def _complete_job(conn: psycopg.Connection, job_id, *, status: str, last_error: Optional[str] = None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.intake_jobs
            SET status = %s, last_error = %s, updated_at = NOW()
            WHERE id = %s;
            """,
            (status, last_error, job_id),
        )
    conn.commit()


def main() -> int:
    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    dsn = _build_dsn()
    _log("worker_start")

    while not _STOP:
        try:
            with psycopg.connect(dsn, connect_timeout=5, row_factory=dict_row) as conn:
                conn.autocommit = False

                job = _fetch_one_job(conn)
                if not job:
                    time.sleep(POLL_SECONDS)
                    continue

                job_id = job["id"]
                attempts = int(job.get("attempt_count") or 0)
                payload = job.get("payload") or {}
                meta = (payload.get("meta") or {}) if isinstance(payload, dict) else {}
                lead = (payload.get("lead") or {}) if isinstance(payload, dict) else {}

                intake_id = str(meta.get("intake_id") or "")
                request_id = str(meta.get("request_id") or "")
                received_at_utc = str(meta.get("received_at_utc") or "")
                lead_source = str(meta.get("lead_source") or "unknown")

                try:
                    # Insert into app.leads using the existing schema-flexible writer.
                    _insert_lead(
                        conn,
                        intake_id=intake_id,
                        request_id=request_id,
                        received_at_utc=received_at_utc,
                        lead_source=lead_source,
                        payload=lead,
                    )

                    _complete_job(conn, job_id, status="done", last_error=None)
                    _log("job_done", job_id=str(job_id), intake_id=intake_id)
                except Exception as e:
                    # Mark failed; if too many attempts, mark dead.
                    err = str(e)
                    final_status = "dead" if attempts >= MAX_ATTEMPTS else "failed"
                    _complete_job(conn, job_id, status=final_status, last_error=err)
                    _log("job_error", job_id=str(job_id), intake_id=intake_id, status=final_status, error=err)

        except Exception as outer:
            _log("worker_loop_error", error=str(outer))
            time.sleep(max(POLL_SECONDS, 1.0))

    _log("worker_stop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
