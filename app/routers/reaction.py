from fastapi import APIRouter, HTTPException, status
from app.schemas.reaction import ReactionCreate, ReactionResponse
from app.crud.reaction import reaction_crud

router = APIRouter()

@router.post("/reactions", response_model=ReactionResponse, status_code=status.HTTP_201_CREATED)
def react(reaction: ReactionCreate):
    reaction_node = reaction_crud.add_or_update_reaction(
        reaction.user_id, reaction.post_id, reaction.type
    )
    if not reaction_node:
        raise HTTPException(status_code=404, detail="User or Post not found")

    return ReactionResponse(
        reaction_id=reaction_node.reaction_id,
        type=reaction_node.type,
        created_at=reaction_node.created_at,
        user_id=reaction.user_id,
        post_id=reaction.post_id
    )


@router.get("/posts/{post_id}/reactions", response_model=list[ReactionResponse])
def get_reactions(post_id: str):
    reactions = reaction_crud.list_reactions_for_post(post_id)
    return [
        ReactionResponse(
            reaction_id=r.reaction_id,
            type=r.type,
            created_at=r.created_at,
            user_id=r.user.single().user_id if r.user else None,
            post_id=post_id
        ) for r in reactions
    ]