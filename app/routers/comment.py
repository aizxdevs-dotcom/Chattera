from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Depends
from uuid import uuid4
import boto3, os
from dotenv import load_dotenv
from typing import Optional, List
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.file import FileResponse
from app.crud.comment import comment_crud
from app.crud.file import file_crud
from app.routers.user import get_current_user   # ✅ import JWT dependency

router = APIRouter()

# ✅ load S3 client
load_dotenv()
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
bucket = os.getenv("AWS_BUCKET_NAME")

# -------------------------------------------------------------------------
# 🔐 Add JSON Comment (authenticated)
# -------------------------------------------------------------------------
@router.post("/comments", response_model=CommentResponse)
def add_comment(
    comment: CommentCreate,
    current_user_id: str = Depends(get_current_user)  # ✅ require token
):
    """
    Add a new comment (authenticated user only).
    The author is derived from the JWT token.
    """
    comment_node = comment_crud.add_comment(
        current_user_id,
        comment.post_id,
        comment.description,
        comment.file_ids
    )
    if not comment_node:
        raise HTTPException(status_code=404, detail="User or Post not found")

    files = [
        FileResponse(
            file_id=f.file_id,
            url=f.url,
            file_type=f.file_type,
            size=f.size,
        )
        for f in comment_node.attachments
    ]

    return CommentResponse(
        comment_id=comment_node.comment_id,
        description=comment_node.description,
        created_at=comment_node.created_at,
        user_id=current_user_id,     # ✅ from token
        post_id=comment.post_id,
        files=files
    )

# -------------------------------------------------------------------------
# 🔐 Add Comment with files (authenticated)
# -------------------------------------------------------------------------
@router.post("/comments/upload", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment_with_files(
    post_id: str = Form(...),
    description: Optional[str] = Form(""),
    files: Optional[List[UploadFile]] = File(None),
    current_user_id: str = Depends(get_current_user)  # ✅ require token
):
    """
    Create a comment with optional file attachments. Requires authentication.
    """
    file_ids, file_responses = [], []

    if files:
        for f in files:
            file_id = str(uuid4())
            object_name = f"{file_id}_{f.filename}"

            # calculate file size
            f.file.seek(0, os.SEEK_END)
            file_size = f.file.tell()
            f.file.seek(0)

            try:
                s3.upload_fileobj(
                    f.file, bucket, object_name,
                    ExtraArgs={"ContentType": f.content_type}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

            file_url = f"https://{bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{object_name}"

            file_node = file_crud.attach_file(
                file_id=file_id,
                url=file_url,
                file_type=f.content_type or "application/octet-stream",
                size=file_size
            )
            if file_node:
                file_ids.append(file_id)
                file_responses.append(FileResponse(
                    file_id=file_id,
                    url=file_url,
                    file_type=f.content_type or "application/octet-stream",
                    size=file_size
                ))

    comment_node = comment_crud.add_comment(
        current_user_id, post_id, description, file_ids  # ✅ secure user source
    )
    if not comment_node:
        raise HTTPException(status_code=404, detail="User or Post not found")

    return CommentResponse(
        comment_id=comment_node.comment_id,
        description=comment_node.description,
        created_at=comment_node.created_at,
        user_id=current_user_id,
        post_id=post_id,
        files=file_responses
    )

# -------------------------------------------------------------------------
# 🟢 Get comments (public)
# -------------------------------------------------------------------------
@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(post_id: str, current_user_id: Optional[str] = None):
    """
    Get all comments for a post (read‑only, public endpoint).
    """
    comments = comment_crud.list_comments_for_post(post_id)
    response = []

    for c in comments:
        files = [
            FileResponse(
                file_id=f.file_id,
                url=f.url,
                file_type=f.file_type,
                size=f.size
            ) for f in c.attachments
        ]

        reactions = comment_crud.get_reaction_counts(c)
        my_reaction = (
            comment_crud.get_user_reaction(c, current_user_id)
            if current_user_id else None
        )

        try:
            user_node = c.user.single()
        except Exception:
            user_node = None

        response.append(CommentResponse(
            comment_id=c.comment_id,
            description=c.description,
            created_at=c.created_at,
            user_id=c.user.single().user_id if c.user else None,
            post_id=post_id,
            username=getattr(user_node, "username", None),
            user_profile_url=getattr(user_node, "profile_photo", None),
            files=files,
            reactions=reactions,
            current_user_reaction=my_reaction
        ))
    return response