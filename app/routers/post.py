from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from uuid import uuid4
import boto3, os
from dotenv import load_dotenv
from typing import List, Optional
from app.schemas.post import PostCreate, PostUpdate, PostResponse, FeedPostResponse
from app.schemas.file import FileResponse
from app.crud.post import post_crud
from app.crud.file import file_crud

router = APIRouter()

# ✅ Load AWS config
load_dotenv()
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
bucket = os.getenv("AWS_BUCKET_NAME")


# ✅ Combined upload endpoint: description + files in one request
@router.post("/posts/upload", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post_with_files(
    user_id: str = Form(...),
    description: Optional[str] = Form(""),
    files: Optional[List[UploadFile]] = File(None)
):
    file_ids = []
    file_responses = []

    if files:
        for file in files:
            file_id = str(uuid4())
            object_name = f"{file_id}_{file.filename}"

            # 👍 calculate file size before upload
            file.file.seek(0, os.SEEK_END)
            file_size = file.file.tell()
            file.file.seek(0)

            try:
                s3.upload_fileobj(
                    file.file, bucket, object_name,
                    ExtraArgs={"ContentType": file.content_type}
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

            file_url = f"https://{bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{object_name}"

            # Create File node in Neo4j
            file_node = file_crud.attach_file(
                file_id=file_id,
                url=file_url,
                file_type=file.content_type or "application/octet-stream",
                size=file_size
            )
            if file_node:
                file_ids.append(file_id)
                file_responses.append(FileResponse(
                    file_id=file_id,
                    url=file_url,
                    file_type=file.content_type or "application/octet-stream",
                    size=file_size
                ))

    # ✅ Create the post
    post_node = post_crud.create_post(
        user_id=user_id,
        description=description,
        file_ids=file_ids
    )
    if not post_node:
        raise HTTPException(status_code=404, detail="User not found")

    return PostResponse(
        post_id=post_node.post_id,
        description=post_node.description,
        created_at=post_node.created_at,
        user_id=user_id,
        files=file_responses
    )


# ✅ Get single post with files
@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: str):
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
            size=f.size
        )
        for f in post_node.attachments
    ]

    return PostResponse(
        post_id=post_node.post_id,
        description=post_node.description,
        created_at=post_node.created_at,
        user_id=user_id,
        files=files
    )


# ✅ Update post (description + files)
@router.put("/posts/{post_id}", response_model=PostResponse)
def update_post(post_id: str, post_update: PostUpdate):
    updated_post = post_crud.update_post(
        post_id,
        description=post_update.description,
        file_ids=post_update.file_ids
    )
    if not updated_post:
        raise HTTPException(status_code=404, detail="Post not found")

    author = updated_post.author.single()

    files = [
        FileResponse(
            file_id=f.file_id,
            url=f.url,
            file_type=f.file_type,
            size=f.size
        )
        for f in updated_post.attachments
    ]

    return PostResponse(
        post_id=updated_post.post_id,
        description=updated_post.description,
        created_at=updated_post.created_at,
        user_id=author.user_id if author else "unknown",
        files=files
    )


# ✅ Delete post
@router.delete("/posts/{post_id}")
def delete_post(post_id: str):
    success = post_crud.delete_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"detail": "Post deleted successfully"}


# ✅ List all posts for a user (with files)
@router.get("/users/{user_id}/posts", response_model=list[PostResponse])
def list_posts_for_user(user_id: str):
    posts = post_crud.list_posts_by_user(user_id)
    return [
        PostResponse(
            post_id=p.post_id,
            description=p.description,
            created_at=p.created_at,
            user_id=user_id,
            files=[
                FileResponse(
                    file_id=f.file_id,
                    url=f.url,
                    file_type=f.file_type,
                    size=f.size
                )
                for f in p.attachments
            ]
        )
        for p in posts
    ]

@router.get("/feed", response_model=List[FeedPostResponse])
def get_global_feed():
    posts = post_crud.list_all_posts()

    feed = []
    for post in posts:
        # Author details
        author_node = post.author.single()
        user_id = author_node.user_id if author_node else None
        username = author_node.username if author_node else None
        email = author_node.email if author_node else None

        # Attachments
        files = [
            FileResponse(
                file_id=f.file_id,
                url=f.url,
                file_type=f.file_type,
                size=f.size
            )
            for f in post.attachments
        ]

        feed.append(FeedPostResponse(
            post_id=post.post_id,
            description=post.description,
            created_at=post.created_at,
            user_id=user_id,
            username=username,
            email=email,
            files=files
        ))

    return feed