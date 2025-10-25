#!/usr/bin/env python3
"""Simple async SendGrid tester.

Usage:
  SENDGRID_API_KEY=... SENDGRID_FROM_EMAIL=... python3 scripts/test_sendgrid.py --to you@example.com

This script will POST to the SendGrid v3 API using httpx. It reads credentials from
the environment and will print the HTTP response code and body on failure.
"""
import os
import sys
import argparse
import asyncio
import json
import httpx


SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL") or os.getenv("SMTP_FROM_EMAIL")


async def send_via_sendgrid(to_email: str, subject: str, html: str) -> int:
    if not SENDGRID_API_KEY:
        print("ERROR: SENDGRID_API_KEY not set in environment.")
        return 1
    if not SENDGRID_FROM_EMAIL:
        print("ERROR: SENDGRID_FROM_EMAIL or SMTP_FROM_EMAIL not set in environment.")
        return 1

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": SENDGRID_FROM_EMAIL},
        "subject": subject,
        "content": [{"type": "text/html", "value": html}],
    }

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }

    timeout = int(os.getenv("SENDGRID_TIMEOUT", 15))
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers)
        return resp.status_code, resp.text


def parse_args():
    p = argparse.ArgumentParser(description="Send a test email via SendGrid API (reads SENDGRID_API_KEY from env)")
    p.add_argument("--to", required=True, help="Recipient email address for the test message")
    p.add_argument("--subject", default="Soceyo SendGrid Test", help="Email subject")
    p.add_argument("--html", default="<p>This is a SendGrid test message.</p>", help="HTML body")
    return p.parse_args()


def main():
    args = parse_args()
    try:
        status_code, body = asyncio.run(send_via_sendgrid(args.to, args.subject, args.html))
    except Exception as e:
        print("Exception while calling SendGrid:", e)
        sys.exit(2)

    if 200 <= status_code < 300:
        print(f"OK: SendGrid returned {status_code}")
        sys.exit(0)
    else:
        print(f"ERROR: SendGrid returned {status_code}")
        # Print body (may contain JSON error details)
        try:
            parsed = json.loads(body)
            print(json.dumps(parsed, indent=2))
        except Exception:
            print(body)
        sys.exit(3)


if __name__ == "__main__":
    main()
