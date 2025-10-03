from fastapi import APIRouter, HTTPException, status
from app.schemas.comment import CommentCreate, CommentResponse
from app.crud.comment import comment_crud

router = APIRouter()

@router.post("/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(comment: CommentCreate):
    comment_node = comment_crud.add_comment(comment.user_id, comment.post_id, comment.text)
    if not comment_node:
        raise HTTPException(status_code=404, detail="User or Post not found")

    return CommentResponse(
        comment_id=comment_node.comment_id,
        text=comment_node.text,
        created_at=comment_node.created_at,
        user_id=comment.user_id,
        post_id=comment.post_id
    )


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
def get_comments(post_id: str):
    comments = comment_crud.list_comments_for_post(post_id)
    return [
        CommentResponse(
            comment_id=c.comment_id,
            text=c.text,
            created_at=c.created_at,
            user_id=c.user.single().user_id if c.user else None,
            post_id=post_id
        )
        for c in comments
    ]