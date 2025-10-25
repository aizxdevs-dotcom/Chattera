from fastapi import APIRouter
import os
import socket
import asyncio

router = APIRouter(prefix="/internal", tags=["internal"])


def _tcp_connect_check(host: str, port: int, timeout: float = 5.0) -> dict:
    res = {"host": host, "port": port, "reachable": False, "error": None}
    try:
        # create_connection will open and close the socket
        with socket.create_connection((host, port), timeout=timeout):
            res["reachable"] = True
    except Exception as e:
        res["error"] = repr(e)
    return res


@router.get("/email-check")
async def email_check():
    """Lightweight TCP-only SMTP connectivity check (no auth attempted).

    Returns JSON: { ok: bool, detail: { host, port, reachable, error } }
    """
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", 587))
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _tcp_connect_check, host, port, 5.0)
    return {"ok": result["reachable"], "detail": result}
