import os
import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, constr
from dotenv import load_dotenv

import psycopg
from psycopg.rows import dict_row

# Load secrets if present
# Quadlet mounts /run/secrets and points EnvironmentFile=/run/secrets/leadgen.env
load_dotenv("/run/secrets/leadgen.env", override=False)

SERVICE_NAME = os.getenv("LEADGEN_SERVICE_NAME", "lead-intake-api")
SERVICE_VERSION = os.getenv("LEADGEN_VERSION", "v1")
ENV_NAME = os.getenv("LEADGEN_ENV", "unknown")

# Auth split (Wave 1): intake and admin-read MUST be separate keys.
# Intake header: X-API-Key
# Admin header:  X-Admin-Key
INTAKE_API_KEY = os.getenv("LEADGEN_INTAKE_API_KEY") or os.getenv("LEADGEN_API_KEY") or os.getenv("LEADGEN_SECRET_KEY")
ADMIN_API_KEY = os.getenv("LEADGEN_ADMIN_API_KEY")

# DB config (Wave 1): durable persistence in Postgres.
# Prefer LEADGEN_DB_DSN. Otherwise build from discrete vars.
DB_DSN = os.getenv("LEADGEN_DB_DSN")
DB_HOST = os.getenv("LEADGEN_DB_HOST", "motorcade-postgres")
DB_PORT = int(os.getenv("LEADGEN_DB_PORT", "5432"))
DB_NAME = os.getenv("LEADGEN_DB_NAME", "motorcade")
DB_USER = os.getenv("LEADGEN_DB_USER", "postgres")
DB_PASSWORD = os.getenv("LEADGEN_DB_PASSWORD")
DB_SSLMODE = os.getenv("LEADGEN_DB_SSLMODE", "disable")

app = FastAPI(title="Motorcade Lead Intake API", version=SERVICE_VERSION)

# --- Idempotency ---
# LEADGEN_07C: enforced via Postgres intake_jobs.idempotency_key (unique) with
# payload match checking at enqueue time.


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    # short-ish but unique enough for v1
    return f"{prefix}_{uuid.uuid4().hex[:18]}"


def _hash_payload(payload: Any) -> str:
    # Stable JSON -> SHA256
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _require_intake_key(x_api_key: Optional[str]) -> None:
    # Health endpoint is unauthenticated; intake requires X-API-Key
    if not INTAKE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "error": {"code": "CONFIG_ERROR", "message": "Intake API key not configured"}},
        )
    if not x_api_key or x_api_key != INTAKE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "error": {"code": "UNAUTHORIZED", "message": "Missing or invalid X-API-Key"}},
        )


def _require_admin_key(x_admin_key: Optional[str]) -> None:
    # Admin read endpoints require X-Admin-Key
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "error": {"code": "CONFIG_ERROR", "message": "Admin API key not configured"}},
        )
    if not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "error": {"code": "UNAUTHORIZED", "message": "Missing or invalid X-Admin-Key"}},
        )


def _build_dsn() -> str:
    if DB_DSN:
        return DB_DSN
    # psycopg DSN string
    parts = [
        f"host={DB_HOST}",
        f"port={DB_PORT}",
        f"dbname={DB_NAME}",
        f"user={DB_USER}",
        f"sslmode={DB_SSLMODE}",
    ]
    if DB_PASSWORD:
        parts.append(f"password={DB_PASSWORD}")
    return " ".join(parts)


_CACHED_LEADS_COLUMNS: Optional[Dict[str, str]] = None  # col_name -> udt_name


def _enqueue_intake_job(
    conn: psycopg.Connection,
    *,
    idempotency_key: Optional[str],
    intake_id: str,
    request_id: str,
    received_at_utc: str,
    lead_source: str,
    payload: Dict[str, Any],
) -> Dict[str, str]:
    """Enqueue a durable intake job.

    LEADGEN_07C contract:
    - /lead/intake returns 202 once the job is durably enqueued.
    - If Idempotency-Key is reused with the same payload, return the original meta.
    - If Idempotency-Key is reused with a different payload, return 409.

    Schema lives in Postgres (app.intake_jobs). We store meta inside the json payload
    to avoid schema drift while still returning stable ids.
    """

    # Wrap payload with meta so the worker can write app.leads without relying on
    in-memory state.
    job_payload = {
        "meta": {
            "intake_id": intake_id,
            "request_id": request_id,
            "received_at_utc": received_at_utc,
            "lead_source": lead_source,
        },
        "lead": payload,
    }
    payload_hash = _hash_payload(job_payload)

    with conn.cursor(row_factory=dict_row) as cur:
        if idempotency_key:
            # If key exists, enforce payload match and return original meta.
            cur.execute(
                """
                SELECT payload
                FROM app.intake_jobs
                WHERE idempotency_key = %s
                LIMIT 1;
                """,
                (idempotency_key,),
            )
            row = cur.fetchone()
            if row is not None:
                existing_payload = row["payload"]
                existing_hash = _hash_payload(existing_payload)
                if existing_hash != payload_hash:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "status": "error",
                            "request_id": request_id,
                            "error": {
                                "code": "IDEMPOTENCY_CONFLICT",
                                "message": "Idempotency-Key reused with different payload",
                                "details": [{"field": "Idempotency-Key", "issue": "payload_mismatch"}],
                            },
                        },
                    )

                meta = (existing_payload or {}).get("meta") or {}
                return {
                    "intake_id": meta.get("intake_id") or intake_id,
                    "request_id": meta.get("request_id") or request_id,
                    "received_at_utc": meta.get("received_at_utc") or received_at_utc,
                }

        # Insert new job
        job_id = uuid.uuid4()
        job_payload_json = json.dumps(job_payload, separators=(",", ":"), ensure_ascii=False)
        cur.execute(
            """
            INSERT INTO app.intake_jobs (id, idempotency_key, payload, status, attempt_count, last_error, created_at, updated_at)
            VALUES (%s, %s, %s::jsonb, 'queued', 0, NULL, NOW(), NOW());
            """,
            (job_id, idempotency_key, job_payload_json),
        )
    conn.commit()
    return {
        "intake_id": intake_id,
        "request_id": request_id,
        "received_at_utc": received_at_utc,
    }


def _get_leads_columns(conn: psycopg.Connection) -> Dict[str, str]:
    global _CACHED_LEADS_COLUMNS
    if _CACHED_LEADS_COLUMNS is not None:
        return _CACHED_LEADS_COLUMNS
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT column_name, udt_name
            FROM information_schema.columns
            WHERE table_schema='app' AND table_name='leads'
            ORDER BY ordinal_position;
            """
        )
        rows = cur.fetchall()
    cols = {r["column_name"]: r["udt_name"] for r in rows}
    if not cols:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "error": {"code": "DB_ERROR", "message": "Table app.leads not found"},
            },
        )
    _CACHED_LEADS_COLUMNS = cols
    return cols


def _pick_json_column(cols: Dict[str, str]) -> Optional[str]:
    # Prefer a clear raw/payload column if present
    preferred = ["raw_payload", "payload", "data", "json", "body"]
    for name in preferred:
        if name in cols:
            return name
    # Otherwise: first jsonb/json column
    for name, typ in cols.items():
        if typ in ("jsonb", "json"):
            return name
    return None


def _insert_lead(conn: psycopg.Connection, *, intake_id: str, request_id: str, received_at_utc: str, lead_source: str, payload: Dict[str, Any]) -> None:
    cols = _get_leads_columns(conn)
    json_col = _pick_json_column(cols)
    if not json_col:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "error": {"code": "DB_ERROR", "message": "No json/jsonb column found on app.leads"},
            },
        )

    # Populate what we can without assuming an exact schema.
    record: Dict[str, Any] = {}
    if "intake_id" in cols:
        record["intake_id"] = intake_id
    if "request_id" in cols:
        record["request_id"] = request_id
    if "lead_source" in cols:
        record["lead_source"] = lead_source
    if "received_at_utc" in cols:
        record["received_at_utc"] = received_at_utc
    if "received_at" in cols:
        record["received_at"] = received_at_utc
    if "created_at" in cols:
        record["created_at"] = received_at_utc

    # Common denormalized fields (optional)
    contact = payload.get("contact") or {}
    req = payload.get("request") or {}
    loc = (req.get("location") or {}) if isinstance(req, dict) else {}

    if "full_name" in cols and isinstance(contact, dict):
        record["full_name"] = contact.get("full_name")
    if "company" in cols and isinstance(contact, dict):
        record["company"] = contact.get("company")
    if "email" in cols and isinstance(contact, dict):
        record["email"] = contact.get("email")
    if "phone" in cols and isinstance(contact, dict):
        record["phone"] = contact.get("phone")
    if "preferred_contact_method" in cols and isinstance(contact, dict):
        record["preferred_contact_method"] = contact.get("preferred_contact_method")
    if "service_type" in cols and isinstance(req, dict):
        record["service_type"] = req.get("service_type")
    if "state" in cols and isinstance(loc, dict):
        record["state"] = loc.get("state")
    if "city" in cols and isinstance(loc, dict):
        record["city"] = loc.get("city")

    # Always store the raw payload in the chosen JSON column.
    # IMPORTANT: Do NOT pass a Python dict directly here.
    # psycopg3 adapter behavior can vary by build; we keep this stable by
    # inserting a JSON string and explicitly casting to jsonb in SQL.
    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    record[json_col] = payload_json

    columns = list(record.keys())
    placeholders: list[str] = []
    values: list[Any] = []
    for c in columns:
        if c == json_col and cols.get(json_col) == "jsonb":
            placeholders.append("%s::jsonb")
        else:
            placeholders.append("%s")
        values.append(record[c])

    sql = f"INSERT INTO app.leads ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

    with conn.cursor() as cur:
        cur.execute(sql, values)
    conn.commit()


# --- Schemas (v1 minimal) ---
PreferredContactMethod = constr(strip_whitespace=True, to_lower=True, pattern=r"^(call|text|email)$")
ServiceType = constr(strip_whitespace=True, to_lower=True, pattern=r"^(armed_security|executive_protection|rapid_response_support|armed_escort_driver|armed_delivery|event_security)$")
RecurrenceType = constr(strip_whitespace=True, to_lower=True, pattern=r"^(one_time|recurring|ongoing_24_7)$")
StateCode = constr(strip_whitespace=True, to_upper=True, min_length=2, max_length=2)


class UTM(BaseModel):
    source: Optional[str] = None
    medium: Optional[str] = None
    campaign: Optional[str] = None


class Context(BaseModel):
    lead_source: Optional[str] = None
    referrer_url: Optional[str] = None
    utm: Optional[UTM] = None


class Location(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: StateCode
    postal_code: Optional[str] = None


class Timeline(BaseModel):
    start_local: str
    end_local: Optional[str] = None


class RequestBody(BaseModel):
    service_type: ServiceType
    timeline: Timeline
    location: Location
    site_type: Optional[str] = None
    notes: Optional[str] = None
    expected_hours: Optional[int] = Field(default=None, ge=1, le=168)
    recurrence: RecurrenceType = "one_time"


class Contact(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    company: Optional[str] = Field(default=None, max_length=160)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=40)
    preferred_contact_method: PreferredContactMethod = "call"


class LeadIntakeRequest(BaseModel):
    contact: Contact
    request: RequestBody
    context: Optional[Context] = None


@app.get("/lead/health")
def lead_health():
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "queue": "pg_outbox",  # LEADGEN_07C: Postgres-only outbox queue
        "db": "configured" if (DB_DSN or DB_HOST) else "missing",
        "time_utc": _now_utc_iso(),
    }


@app.get("/version")
def version():
    # Optional, internal convenience (also used for auditability)
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "env": ENV_NAME,
        "git_sha": os.getenv("LEADGEN_GIT_SHA", "unknown"),
        "build_time": os.getenv("LEADGEN_BUILD_TIME", "unknown"),
    }


@app.post("/lead/intake", status_code=202)
async def lead_intake(
    payload: LeadIntakeRequest,
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
    x_lead_source: Optional[str] = Header(default=None, alias="X-Lead-Source"),
):
    _require_intake_key(x_api_key)

    # Deterministic v1 doctrine constraint: Texas-only
    if payload.request.location.state.upper() != "TX":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "status": "error",
                "request_id": x_request_id or _new_id("req"),
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Texas-only launch (v1)",
                    "details": [{"field": "request.location.state", "issue": "must_equal_TX"}],
                },
            },
        )

    req_id = x_request_id or _new_id("req")
    received_at = _now_utc_iso()

    # Normalize lead source (header overrides body context if present)
    lead_source = (x_lead_source or (payload.context.lead_source if payload.context else None) or "unknown").strip()

    intake_id = _new_id("li")

    # Durable enqueue (LEADGEN_07C): write to app.intake_jobs.
    # This is the key contract: a lead is not "accepted" unless it's durably queued.
    dsn = _build_dsn()
    try:
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            meta = _enqueue_intake_job(
                conn,
                idempotency_key=idempotency_key,
                intake_id=intake_id,
                request_id=req_id,
                received_at_utc=received_at,
                lead_source=lead_source,
                payload=payload.model_dump(),
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "request_id": req_id,
                "error": {"code": "DB_ERROR", "message": "Failed to enqueue intake job", "details": str(e)},
            },
        )

    # Queue-first behavior: enqueue is currently a stub (wired in PLAT_04)
    # We still behave as if accepted/queued.
    # Minimal observability (stdout logs): structured-ish single line.
    client_host = request.client.host if request.client else None
    print(json.dumps({
        "event": "lead_intake_accepted",
        "request_id": req_id,
        "intake_id": meta.get("intake_id"),
        "lead_source": lead_source,
        "idempotency_key_present": bool(idempotency_key),
        "client_ip": client_host,
        "time_utc": received_at,
    }, separators=(",", ":"), sort_keys=True))

    return {
        "status": "accepted",
        "intake_id": meta.get("intake_id"),
        "request_id": meta.get("request_id"),
        "received_at_utc": meta.get("received_at_utc"),
    }


@app.get("/admin/leads")
def admin_list_leads(
    limit: int = 50,
    offset: int = 0,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
):
    _require_admin_key(x_admin_key)
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    dsn = _build_dsn()
    with psycopg.connect(dsn, connect_timeout=5, row_factory=dict_row) as conn:
        cols = _get_leads_columns(conn)
        json_col = _pick_json_column(cols)

        # Prefer a stable sort column if present
        order_col = "created_at" if "created_at" in cols else ("received_at_utc" if "received_at_utc" in cols else "intake_id")

        # Select a minimal safe view.
        select_cols = []
        for c in ["intake_id", "request_id", "lead_source", "created_at", "received_at_utc", "email", "phone", "full_name", "service_type", "city", "state"]:
            if c in cols:
                select_cols.append(c)
        if not select_cols and json_col:
            select_cols = [json_col]

        sql = f"SELECT {', '.join(select_cols)} FROM app.leads ORDER BY {order_col} DESC LIMIT %s OFFSET %s"
        with conn.cursor() as cur:
            cur.execute(sql, (limit, offset))
            rows = cur.fetchall()

    return {"status": "ok", "count": len(rows), "limit": limit, "offset": offset, "leads": rows}


@app.get("/admin/leads/{lead_id}")
def admin_get_lead(
    lead_id: str,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
):
    _require_admin_key(x_admin_key)
    dsn = _build_dsn()
    with psycopg.connect(dsn, connect_timeout=5, row_factory=dict_row) as conn:
        cols = _get_leads_columns(conn)
        json_col = _pick_json_column(cols)

        # Try lookup by intake_id first (most likely), then by id if present.
        where_clauses = []
        params = []
        if "intake_id" in cols:
            where_clauses.append("intake_id = %s")
            params.append(lead_id)
        if "id" in cols:
            where_clauses.append("id::text = %s")
            params.append(lead_id)
        if not where_clauses:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "error", "error": {"code": "DB_ERROR", "message": "No id/intake_id column on app.leads"}},
            )

        select_cols = list(cols.keys())
        if json_col and json_col in select_cols:
            # json column already included
            pass

        sql = f"SELECT {', '.join(select_cols)} FROM app.leads WHERE ({' OR '.join(where_clauses)}) LIMIT 1"
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error", "error": {"code": "NOT_FOUND", "message": "Lead not found"}},
        )
    return {"status": "ok", "lead": row}
