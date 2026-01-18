import os
from fastapi import FastAPI
from dotenv import load_dotenv

# Load secrets if present
# Quadlet mounts /run/secrets and points EnvironmentFile=/run/secrets/leadgen.env
load_dotenv("/run/secrets/leadgen.env", override=False)

app = FastAPI(title="Motorcade LeadGen API", version=os.getenv("LEADGEN_VERSION", "0.0.0"))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {
        "service": "leadgen-api",
        "version": os.getenv("LEADGEN_VERSION", "0.0.0"),
        "env": os.getenv("LEADGEN_ENV", "unknown"),
    }
