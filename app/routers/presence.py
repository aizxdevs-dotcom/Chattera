from fastapi import APIRouter, Depends
from app.services.presence_manager import mark_user_active, get_active_user_ids
from app.models.user import User
from typing import Optional
from app.schemas.conversation import ConversationMember
from app.routers.user import get_current_user   # 👈 for identifying the caller

router = APIRouter(tags=["Presence"])


@router.get("/active-users", response_model=list[ConversationMember])
async def list_active_users(
    current_user_id: Optional[str] = Depends(get_current_user)
):
    """
    🔓 Public endpoint — anyone can view all active users.
    If a valid JWT token is provided, the user's online presence is automatically refreshed.
    """
    # ✅ If user is authenticated, mark them active automatically
    if current_user_id:
        await mark_user_active(current_user_id)

    # ✅ Fetch all active user IDs from Redis
    ids = await get_active_user_ids()
    users: list[ConversationMember] = []

    # ✅ Build the response model
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