# Motorcade LeadGen — Fix: email-validator missing in container

## What this patch does
- Ensures the API container dependencies include the EmailStr validation extras required by Pydantic.
- Adds a build-time sanity check so the image build fails early if `email_validator` is missing.

## Files changed
- `app/api/requirements.txt`
- `app/api/Containerfile`

## Apply
1) Unzip this into your **motorcade-leadgen** repo root (merge/overwrite).
2) Commit the change.
3) Re-run PLAT_04 from the infra repo (it will git pull and rebuild the image).

## Expected result
- `podman build` succeeds
- container stays running
- `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/lead/health` returns `200`
