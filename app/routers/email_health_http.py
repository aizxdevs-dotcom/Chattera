from fastapi import APIRouter
import asyncio
import urllib.request
import urllib.error
import os
import logging

from app.services.mail_api_provider import SENDGRID_API_KEY

router = APIRouter(prefix="/internal", tags=["internal"])

logger = logging.getLogger(__name__)


def _sendgrid_head_check(url: str, api_key: str | None, timeout: float = 5.0) -> dict:
    """Sync HEAD check to SendGrid root. Returns a dict with result details.

    This uses HEAD so it's lightweight. If an API key is present we send it so the
    response reflects authenticated reachability (401/403 means network OK).
    """
    result = {"url": url, "reachable": False, "status": None, "error": None}
    headers = {"User-Agent": "Chattera/SendGrid-Health-Check"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, method="HEAD", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["status"] = resp.getcode()
            result["reachable"] = True
            return result
    except urllib.error.HTTPError as he:
        # Auth errors (401/403) still indicate network reachability
        result["status"] = getattr(he, 'code', None)
        result["error"] = f"HTTPError: {repr(he)}"
        # mark reachable when we have an HTTP status (even 401/403)
        if result["status"] is not None:
            result["reachable"] = True
        return result
    except Exception as exc:
        result["error"] = repr(exc)
        return result


@router.get("/email-sendgrid-check")
async def email_sendgrid_check():
    """Lightweight HTTP check to verify outbound connectivity to SendGrid API.

    Returns JSON: { ok: bool, detail: { url, reachable, status, error } }
    - ok: True if we could establish HTTP-level connectivity (even if 401/403).
    """
    # Use the SendGrid API root; it's stable and responds quickly.
    url = os.getenv("SENDGRID_HEALTH_URL", "https://api.sendgrid.com/v3/")
    timeout = float(os.getenv("SENDGRID_TIMEOUT", "5.0"))
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _sendgrid_head_check, url, SENDGRID_API_KEY, timeout)
    return {"ok": bool(result.get("reachable")), "detail": result}


@router.get("/email-check")
async def email_check_alias():
    """Compatibility alias: previously `/internal/email-check` tested SMTP TCP reachability.

    Now it maps to the SendGrid HTTP check so tooling that still calls the old path
    continues to receive a useful response.
    """
    return await email_sendgrid_check()
