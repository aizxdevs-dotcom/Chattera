from fastapi import APIRouter

# Deprecated: this TCP SMTP health endpoint is retained for backwards compatibility
# but it is no longer used. Use `/internal/email-sendgrid-check` to verify
# outbound HTTP connectivity to the SendGrid API.

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/email-check")
async def email_check_deprecated():
    return {"ok": False, "detail": "deprecated; use /internal/email-sendgrid-check"}
