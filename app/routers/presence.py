from fastapi import APIRouter
from app.services.presence_manager import get_active_user_ids
from app.models.user import User
from app.schemas.conversation import ConversationMember  # or a similar user schema

router = APIRouter(tags=["Presence"])

@router.get("/active-users", response_model=list[ConversationMember])
async def list_active_users():
    """
    Return all users currently marked active in Redis.
    Each item includes user_id, username, profile photo, and is_active flag.
    """
    ids = await get_active_user_ids()
    users: list[ConversationMember] = []

    for uid in ids:
        u = User.nodes.get_or_none(user_id=uid)
        if u:
            users.append(
                ConversationMember(
                    user_id=u.user_id,
                    username=u.username,
                    user_profile_url=u.profile_photo,
                    is_active=True,
                )
            )

    return users