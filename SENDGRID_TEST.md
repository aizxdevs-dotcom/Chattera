SendGrid quick test (safe, no secrets in repo)
=============================================

Overview
This document explains how to safely test SendGrid from your local dev environment or deployment without committing secrets.

Preconditions

Environment variables (example)
Set these in your shell or deployment environment:

```bash
export SENDGRID_API_KEY="<your-sendgrid-api-key>"
export SENDGRID_FROM_EMAIL="no-reply@yourdomain.com"
```

Run the included test script
From the repository root run:

```bash
# install deps if needed
pip install -r requirements.txt

# run test (replace with a recipient you control)
SENDGRID_API_KEY="$SENDGRID_API_KEY" SENDGRID_FROM_EMAIL="$SENDGRID_FROM_EMAIL" python3 scripts/test_sendgrid.py --to your_test_email@example.com
```

Expected results

If you see 401/403

Security notes (important)

Optional: Use the official sendgrid-python SDK
If you'd rather use the official SDK, install `sendgrid` and use the example in SendGrid's dashboard — the API key usage is identical (the script here uses httpx to avoid adding another SDK).
SendGrid tests removed

The SendGrid quick test was removed from the repository and should be recreated locally if you need to test SendGrid. Do NOT commit API keys or secrets. Instead, run tests locally and set `SENDGRID_API_KEY` in your shell while testing.

If you want, I can add a secure local test helper (that you run manually) or an example for how to test SMTP connectivity instead.