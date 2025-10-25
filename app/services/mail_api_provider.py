import os
import json
import urllib.request
import urllib.error
import asyncio
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL") or os.getenv("SMTP_FROM_EMAIL")
MAIL_PROVIDER = os.getenv("MAIL_PROVIDER", "sendgrid").lower()


def _send_via_sendgrid_sync(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: Optional[str] = None,
    timeout: int = 15,
) -> Tuple[int, bytes]:
    """Blocking sync POST to SendGrid v3 using stdlib urllib."""
    if not SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY not configured")
    from_email = from_email or SENDGRID_FROM_EMAIL
    if not from_email:
        raise RuntimeError("from_email is required (SENDGRID_FROM_EMAIL or SMTP_FROM_EMAIL)")

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_body}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SENDGRID_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Chattera/SendGrid-StdLib",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            body = resp.read()
            logger.info("SendGrid: sent email to %s (status=%s)", to_email, status)
            return status, body
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        logger.warning("SendGrid HTTPError %s: %s", getattr(e, "code", None), body)
        return getattr(e, "code", 500), body
    except Exception as exc:
        logger.exception("SendGrid send failed: %s", exc)
        raise


async def send_email_async(
    to_email: str,
    subject: str,
    html_body: str,
    from_email: Optional[str] = None,
    timeout: int = 15,
) -> Tuple[bool, int, bytes]:
    """
    Async wrapper. Returns (ok, status_code, response_body).
    Uses stdlib and run_in_executor to avoid extra deps.
    """
    loop = asyncio.get_running_loop()
    try:
        status, body = await loop.run_in_executor(
            None, _send_via_sendgrid_sync, to_email, subject, html_body, from_email, timeout
        )
        return 200 <= status < 300, status, body
    except Exception as exc:
        logger.exception("SendGrid send exception: %s", exc)
        return False, 0, str(exc).encode()
