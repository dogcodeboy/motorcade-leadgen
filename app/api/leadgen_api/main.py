import os
import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, constr
from dotenv import load_dotenv

# Load secrets if present
# Quadlet mounts /run/secrets and points EnvironmentFile=/run/secrets/leadgen.env
load_dotenv("/run/secrets/leadgen.env", override=False)

SERVICE_NAME = os.getenv("LEADGEN_SERVICE_NAME", "lead-intake-api")
SERVICE_VERSION = os.getenv("LEADGEN_VERSION", "v1")
ENV_NAME = os.getenv("LEADGEN_ENV", "unknown")

# API Key (shared secret). Inject via vault -> env file.
API_KEY = os.getenv("LEADGEN_API_KEY") or os.getenv("LEADGEN_SECRET_KEY")  # allow legacy naming

app = FastAPI(title="Motorcade Lead Intake API", version=SERVICE_VERSION)

# --- Idempotency (in-memory for now; replace with Redis/DB later) ---
# Map: idempotency_key -> payload_hash, intake_id, request_id, received_at_utc
_IDEMPOTENCY_STORE: Dict[str, Dict[str, str]] = {}


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    # short-ish but unique enough for v1
    return f"{prefix}_{uuid.uuid4().hex[:18]}"


def _hash_payload(payload: Any) -> str:
    # Stable JSON -> SHA256
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _require_api_key(x_api_key: Optional[str]) -> None:
    # Health endpoint is unauthenticated; everything else requires X-API-Key
    if not API_KEY:
        # Misconfiguration should fail closed.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "error": {"code": "CONFIG_ERROR", "message": "API key not configured"}},
        )
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "error": {"code": "UNAUTHORIZED", "message": "Missing or invalid X-API-Key"}},
        )


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
        "queue": "stub",  # queue-first; real queue wired in PLAT_04
        "db_readonly_check": "optional",
        "time_utc": _now_utc_iso(),
    }


@app.get("/version")
def version():
    # Optional, internal convenience
    return {"service": SERVICE_NAME, "version": SERVICE_VERSION, "env": ENV_NAME}


@app.post("/lead/intake", status_code=202)
async def lead_intake(
    payload: LeadIntakeRequest,
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
    x_lead_source: Optional[str] = Header(default=None, alias="X-Lead-Source"),
):
    _require_api_key(x_api_key)

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

    # Idempotency handling
    if idempotency_key:
        payload_hash = _hash_payload(payload.model_dump())
        prior = _IDEMPOTENCY_STORE.get(idempotency_key)
        if prior:
            if prior["payload_hash"] != payload_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "status": "error",
                        "request_id": req_id,
                        "error": {
                            "code": "IDEMPOTENCY_CONFLICT",
                            "message": "Idempotency-Key reused with different payload",
                            "details": [{"field": "Idempotency-Key", "issue": "payload_mismatch"}],
                        },
                    },
                )
            # Return original IDs (stable response)
            return {
                "status": "accepted",
                "intake_id": prior["intake_id"],
                "request_id": prior["request_id"],
                "received_at_utc": prior["received_at_utc"],
            }

        intake_id = _new_id("li")
        _IDEMPOTENCY_STORE[idempotency_key] = {
            "payload_hash": payload_hash,
            "intake_id": intake_id,
            "request_id": req_id,
            "received_at_utc": received_at,
        }
    else:
        intake_id = _new_id("li")

    # Queue-first behavior: enqueue is currently a stub (wired in PLAT_04)
    # We still behave as if accepted/queued.
    # Minimal observability (stdout logs): structured-ish single line.
    client_host = request.client.host if request.client else None
    print(json.dumps({
        "event": "lead_intake_accepted",
        "request_id": req_id,
        "intake_id": intake_id,
        "lead_source": lead_source,
        "idempotency_key_present": bool(idempotency_key),
        "client_ip": client_host,
        "time_utc": received_at,
    }, separators=(",", ":"), sort_keys=True))

    return {
        "status": "accepted",
        "intake_id": intake_id,
        "request_id": req_id,
        "received_at_utc": received_at,
    }
