from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer
from typing import List

from app.schemas.notification import NotificationResponse
from app.crud.notification import notification_crud
from app.crud.user import user_crud
from app.crud.post import post_crud
from app.config import verify_access_token

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(token=Security(bearer_scheme)) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_access_token(token.credentials)
    return payload["sub"]


@router.get("/notifications", response_model=List[NotificationResponse])
def get_my_notifications(current_user_id: str = Depends(get_current_user_id)):
    """Return all notifications for the authenticated user."""
    notifs = notification_crud.list_for_user(current_user_id)
    response = []
    for n in notifs:
        sender = user_crud.get_user_by_id(n.sender_id)
        post = post_crud.get_post(n.post_id)
        response.append(
            NotificationResponse(
                notification_id=n.notification_id,
                receiver_id=n.receiver_id,
                sender_id=n.sender_id,
                post_id=n.post_id,
                type=n.type,
                message=n.message,
                created_at=n.created_at,
                is_read=n.is_read,
                sender_username=getattr(sender, "username", None),
                sender_profile_photo_url=getattr(sender, "profile_photo", None),
                post_description=getattr(post, "description", None),
            )
        )
    return response


@router.put("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: str, current_user_id: str = Depends(get_current_user_id)):
    notif = notification_crud.mark_as_read(notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notif.receiver_id != current_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    sender = user_crud.get_user_by_id(notif.sender_id)
    post = post_crud.get_post(notif.post_id)
    return NotificationResponse(
        notification_id=notif.notification_id,
        receiver_id=notif.receiver_id,
        sender_id=notif.sender_id,
        post_id=notif.post_id,
        type=notif.type,
        message=notif.message,
        created_at=notif.created_at,
        is_read=notif.is_read,
        sender_username=getattr(sender, "username", None),
        sender_profile_photo=getattr(sender, "profile_photo", None),
        post_description=getattr(post, "description", None),
    )