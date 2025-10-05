from fastapi import (
    APIRouter, HTTPException, Query, status,
    UploadFile, File, Form, Depends, Security
)
from uuid import uuid4
import boto3, os
from dotenv import load_dotenv
from typing import List, Optional
from fastapi.security import HTTPBearer

from app.schemas.post import PostCreate, PostUpdate, PostResponse, FeedPostResponse
from app.schemas.file import FileResponse
from app.schemas.comment import CommentResponse
from app.crud.comment import comment_crud
from app.crud.post import post_crud
from app.crud.file import file_crud
from app.crud.user import user_crud                     # ✅ correct import
from app.config import verify_access_token


router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


# ------------ Helpers ---------------------------------------------------------
def get_current_user(token=Security(bearer_scheme)) -> str:
    """Extract and verify JWT token credentials."""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_access_token(token.credentials)
    return payload["sub"]


# ------------ S3 setup --------------------------------------------------------
load_dotenv()
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
bucket = os.getenv("AWS_BUCKET_NAME")


# -----------------------------------------------------------------------------
@router.post("/posts/upload", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post_with_files(
    description: Optional[str] = Form(""),
    files: Optional[List[UploadFile]] = File(None),
    current_user_id: str = Depends(get_current_user),
):
    """
    Create a new post (with optional files). Only available to authenticated users.
    """
    file_ids: List[str] = []
    file_responses: List[FileResponse] = []

    # ---- Upload files to S3 --------------------------------------------------
    if files:
        for file in files:
            file_id = str(uuid4())
            object_name = f"{file_id}_{file.filename}"

            # determine file size
            file.file.seek(0, os.SEEK_END)
            file_size = file.file.tell()
            file.file.seek(0)

            try:
                s3.upload_fileobj(
                    file.file,
                    bucket,
                    object_name,               # ✅ was 'filename'
                    ExtraArgs={
                        "ContentType": file.content_type,
                                 
                    },
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")

            file_url = (
                f"https://{bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{object_name}"
            )

            file_node = file_crud.attach_file(
                file_id=file_id,
                url=file_url,
                file_type=file.content_type or "application/octet-stream",
                size=file_size,
            )
            if file_node:
                file_ids.append(file_id)
                file_responses.append(
                    FileResponse(
                        file_id=file_id,
                        url=file_url,
                        file_type=file.content_type or "application/octet-stream",
                        size=file_size,
                    )
                )

    # ---- Create the post node ------------------------------------------------
    post_node = post_crud.create_post(
        user_id=current_user_id,
        description=description,
        file_ids=file_ids,
    )
    if not post_node:
        raise HTTPException(status_code=404, detail="User not found")

    return PostResponse(
        post_id=post_node.post_id,
        description=post_node.description,
        created_at=post_node.created_at,
        user_id=current_user_id,
        files=file_responses,
    )


# -----------------------------------------------------------------------------
@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: str, current_user_id: str = Depends(get_current_user)):
    """Get a specific post (authenticated users only)."""
    post_node = post_crud.get_post(post_id)
    if not post_node:
        raise HTTPException(status_code=404, detail="Post not found")

    author_node = post_node.author.single()
    user_id = author_node.user_id if author_node else None

    files = [
        FileResponse(
            file_id=f.file_id,
            url=f.url,
            file_type=f.file_type,
            size=f.size,
        )
        for f in post_node.attachments
    ]

    comments = []
    for c in post_node.comments.order_by("created_at"):
        files_attached = [
            FileResponse(
                file_id=f.file_id,
                url=f.url,
                file_type=f.file_type,
                size=f.size,
            )
            for f in c.attachments
        ]
        comment_reactions = comment_crud.get_reaction_counts(c)
        my_comment_reaction = comment_crud.get_user_reaction(c, current_user_id)
        comments.append(
            CommentResponse(
                comment_id=c.comment_id,
                description=c.description,
                created_at=c.created_at,
                user_id=c.user.single().user_id if c.user else None,
                post_id=post_node.post_id,
                files=files_attached,
                reactions=comment_reactions,
                current_user_reaction=my_comment_reaction,
            )
        )

    reactions = post_crud.get_reaction_counts(post_node)
    my_reaction = post_crud.get_user_reaction(post_node, current_user_id)
    return PostResponse(
        post_id=post_node.post_id,
        description=post_node.description,
        created_at=post_node.created_at,
        user_id=user_id,
        files=files,
        comments=comments,
        reactions=reactions,
        current_user_reaction=my_reaction,
    )


# -----------------------------------------------------------------------------
@router.put("/posts/{post_id}", response_model=PostResponse)
def update_post(
    post_id: str,
    post_update: PostUpdate,
    current_user_id: str = Depends(get_current_user),
):
    """Update only the description of a post (author‑only)."""
    post_node = post_crud.get_post(post_id)
    if not post_node:
        raise HTTPException(status_code=404, detail="Post not found")

    author = post_node.author.single()
    if not author or author.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You may only edit your own posts")

    updated_post = post_crud.update_post(
        post_id,
        description=post_update.description,
        file_ids=None,
    )

    return PostResponse(
        post_id=updated_post.post_id,
        description=updated_post.description,
        created_at=updated_post.created_at,
        user_id=author.user_id,
        files=[
            FileResponse(
                file_id=f.file_id,
                url=f.url,
                file_type=f.file_type,
                size=f.size,
            )
            for f in updated_post.attachments
        ],
    )


# -----------------------------------------------------------------------------
@router.delete("/posts/{post_id}")
def delete_post(post_id: str, current_user_id: str = Depends(get_current_user)):
    """Delete a post (only the author can delete)."""
    post = post_crud.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    author = post.author.single()
    if not author or author.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="You may only delete your own posts")

    success = post_crud.delete_post(post_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete post")

    return {"detail": "Post deleted successfully"}


# -----------------------------------------------------------------------------
@router.get("/feed", response_model=List[FeedPostResponse])
def get_global_feed(current_user_id: Optional[str] = Query(default=None)):
    """Return global feed with author info, files, comments, and reactions."""
    posts = post_crud.list_all_posts()
    feed = []

    for post in posts:
        # --- Author information ---
        author_node = post.author.single()
        user_id = getattr(author_node, "user_id", None)
        username = getattr(author_node, "username", None)
        email = getattr(author_node, "email", None)
        profile_url = getattr(author_node, "profile_photo", None)

        # --- Post files ---
        files = [
            FileResponse(
                file_id=f.file_id,
                url=f.url,
                file_type=f.file_type,
                size=f.size,
            )
            for f in post.attachments
        ]

        # --- Comments (with commenter info & attachments) ---
        comments = []
        for c in post.comments.order_by("created_at"):
            user_node = None
            try:
                user_node = c.user.single()
            except Exception:
                user_node = None

            commenter_id = getattr(user_node, "user_id", None)
            commenter_name = getattr(user_node, "username", None)
            commenter_photo = getattr(user_node, "profile_photo", None)

            files_attached = [
                FileResponse(
                    file_id=f.file_id,
                    url=f.url,
                    file_type=f.file_type,
                    size=f.size,
                )
                for f in c.attachments
            ]

            comment_reactions = comment_crud.get_reaction_counts(c)
            my_comment_reaction = (
                comment_crud.get_user_reaction(c, current_user_id)
                if current_user_id
                else None
            )

            comments.append(
                CommentResponse(
                    comment_id=c.comment_id,
                    description=c.description,
                    created_at=c.created_at,
                    user_id=commenter_id,
                    post_id=post.post_id,
                    username=commenter_name,
                    user_profile_url=commenter_photo,
                    files=files_attached,
                    reactions=comment_reactions,
                    current_user_reaction=my_comment_reaction,
                )
            )

        # --- Post reactions ---
        post_reactions = post_crud.get_reaction_counts(post)
        my_reaction = (
            post_crud.get_user_reaction(post, current_user_id)
            if current_user_id
            else None
        )

        # --- Build feed item ---
        feed.append(
            FeedPostResponse(
                post_id=post.post_id,
                description=post.description,
                created_at=post.created_at,
                user_id=user_id,
                username=username,
                email=email,
                user_profile_url=profile_url,  # ✅ include author’s avatar
                files=files,
                comments=comments,
                reactions=post_reactions,
                current_user_reaction=my_reaction,
            )
        )

    return feed

# -----------------------------------------------------------------------------
@router.get("/users/{user_id}/posts", response_model=List[PostResponse])
def list_posts_for_user(user_id: str, current_user_id: str = Depends(get_current_user)):
    """List posts for a specific user (requires authentication)."""
    posts = post_crud.list_posts_by_user(user_id)
    if not posts:
        raise HTTPException(status_code=404, detail="No posts found for this user")

    user = user_crud.get_user_by_id(user_id)
    username = user.username if user else None
    email = user.email if user else None

    return [
        PostResponse(
            post_id=p.post_id,
            description=p.description,
            created_at=p.created_at,
            user_id=user_id,
            username=username,
            email=email,
            files=[
                FileResponse(
                    file_id=f.file_id,
                    url=f.url,
                    file_type=f.file_type,
                    size=f.size,
                )
                for f in p.attachments
            ],
        )
        for p in posts
    ]