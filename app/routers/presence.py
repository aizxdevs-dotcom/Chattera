from fastapi import APIRouter, Depends
from app.services.presence_manager import mark_user_active, get_active_user_ids
from app.models.user import User
from app.schemas.conversation import ConversationMember
from app.routers.user import get_current_user   # 👈 for identifying the caller

router = APIRouter(prefix="/api", tags=["Presence"])


@router.get("/active-users", response_model=list[ConversationMember])
async def list_active_users(current_user_id: str = Depends(get_current_user)):
    """
    Return all users currently marked active in Redis.
    Also refresh the TTL for the calling user so they stay marked online.
    """
    # 1️⃣ Mark the current requester as active
    await mark_user_active(current_user_id)

    # 2️⃣ Fetch all keys (currently online users)
    ids = await get_active_user_ids()
    users: list[ConversationMember] = []

    # 3️⃣ Build the response model
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