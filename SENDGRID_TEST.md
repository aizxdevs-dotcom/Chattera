SendGrid quick test (safe, no secrets in repo)
=============================================

Overview
--------
This document explains how to safely test SendGrid from your local dev environment or deployment without committing secrets.

Preconditions
-------------
- You must create a SendGrid API key (Mail Send permission) in the SendGrid dashboard and copy it once.
- Do NOT commit the API key into git. Use environment variables or your platform's secret manager.

Environment variables (example)
--------------------------------
Set these in your shell or deployment environment:

```bash
export SENDGRID_API_KEY="<your-sendgrid-api-key>"
export SENDGRID_FROM_EMAIL="no-reply@yourdomain.com"
```

Run the included test script
---------------------------
From the repository root run:

```bash
# install deps if needed
pip install -r requirements.txt

# run test (replace with a recipient you control)
SENDGRID_API_KEY="$SENDGRID_API_KEY" SENDGRID_FROM_EMAIL="$SENDGRID_FROM_EMAIL" python3 scripts/test_sendgrid.py --to your_test_email@example.com
```

Expected results
----------------
- On success the script prints: `OK: SendGrid returned 202` and you should receive the test email.
- On failure the script prints `ERROR: SendGrid returned <code>` and the response body (JSON) with details (e.g., invalid API key, missing permissions).

If you see 401/403
-----------------
- 401/403 means the API key is invalid or lacks permissions. Recreate a new key with Mail Send permission and update the `SENDGRID_API_KEY` env var.

Security notes (important)
--------------------------
- Rotate any API key that was accidentally pasted into the repo or shared publicly.
- Use separate keys for dev/staging/production.
- Use your host's secret manager (Render/Heroku/Vercel/AWS Secrets Manager) for production keys.

Optional: Use the official sendgrid-python SDK
--------------------------------------------
If you'd rather use the official SDK, install `sendgrid` and use the example in SendGrid's dashboard — the API key usage is identical (the script here uses httpx to avoid adding another SDK).