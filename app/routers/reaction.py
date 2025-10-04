from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.reaction import ReactionCreate, ReactionResponse
from app.crud.reaction import reaction_crud
from app.routers.user import get_current_user   # ✅ import your JWT dependency

router = APIRouter()


# -------------------------------------------------------------------------
# 🔐 Create or update reaction (authenticated)
# -------------------------------------------------------------------------
@router.post("/reactions", response_model=ReactionResponse, status_code=status.HTTP_201_CREATED)
def react(
    reaction: ReactionCreate,
    current_user_id: str = Depends(get_current_user)   # ✅ require token
):
    """
    Add or update a reaction for a post. Requires authentication.
    The user_id is derived from the JWT token for security.
    """
    reaction_node = reaction_crud.add_or_update_reaction(
        current_user_id, reaction.post_id, reaction.type  # ✅ user_id comes from token
    )
    if not reaction_node:
        raise HTTPException(status_code=404, detail="User or Post not found")

    return ReactionResponse(
        reaction_id=reaction_node.reaction_id,
        type=reaction_node.type,
        created_at=reaction_node.created_at,
        user_id=current_user_id,
        post_id=reaction.post_id
    )


# -------------------------------------------------------------------------
# 🟢 Get all reactions for a post (public)
# -------------------------------------------------------------------------
@router.get("/posts/{post_id}/reactions", response_model=list[ReactionResponse])
def get_reactions(post_id: str):
    """
    Retrieve all reactions for a specific post.
    Public access — no token required.
    """
    reactions = reaction_crud.list_reactions_for_post(post_id)
    return [
        ReactionResponse(
            reaction_id=r.reaction_id,
            type=r.type,
            created_at=r.created_at,
            user_id=r.user.single().user_id if r.user else None,
            post_id=post_id
        )
        for r in reactions
    ]