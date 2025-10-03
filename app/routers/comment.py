from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from uuid import uuid4
import boto3, os
from dotenv import load_dotenv
from typing import Optional, List
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.file import FileResponse
from app.crud.comment import comment_crud
from app.crud.file import file_crud

router = APIRouter()

# ✅ load s3 client
load_dotenv()
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
bucket = os.getenv("AWS_BUCKET_NAME")


# JSON endpoint
@router.post("/comments", response_model=CommentResponse)
def add_comment(comment: CommentCreate):
    comment_node = comment_crud.add_comment(
        comment.user_id,
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
        user_id=comment.user_id,
        post_id=comment.post_id,
        files=files
    )

@router.post("/comments/upload", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment_with_files(
    user_id: str = Form(...),
    post_id: str = Form(...),
    description: Optional[str] = Form(""),
    files: Optional[List[UploadFile]] = File(None)
):
    file_ids = []
    file_responses = []

    if files:
        for f in files:
            file_id = str(uuid4())
            object_name = f"{file_id}_{f.filename}"

            # find file size
            f.file.seek(0, os.SEEK_END)
            file_size = f.file.tell()
            f.file.seek(0)

            s3.upload_fileobj(f.file, bucket, object_name, ExtraArgs={"ContentType": f.content_type})

            file_url = f"https://{bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{object_name}"

            # Neo4j File node
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

    comment_node = comment_crud.add_comment(user_id, post_id, description, file_ids)
    if not comment_node:
        raise HTTPException(status_code=404, detail="User or Post not found")

    return CommentResponse(
        comment_id=comment_node.comment_id,
        description=comment_node.description,
        created_at=comment_node.created_at,
        user_id=user_id,
        post_id=post_id,
        files=file_responses
    )

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(post_id: str, current_user_id: Optional[str] = None):
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

        # 🆕 reactions
        reactions = comment_crud.get_reaction_counts(c)
        my_reaction = (
            comment_crud.get_user_reaction(c, current_user_id)
            if current_user_id else None
        )

        response.append(CommentResponse(
            comment_id=c.comment_id,
            description=c.description,
            created_at=c.created_at,
            user_id=c.user.single().user_id if c.user else None,
            post_id=post_id,
            files=files,
            reactions=reactions,
            current_user_reaction=my_reaction
        ))
    return response