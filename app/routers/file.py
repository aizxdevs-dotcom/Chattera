from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
from uuid import uuid4
import boto3, os
from dotenv import load_dotenv
from app.schemas.file import FileResponse, FileUpdate
from app.crud.file import file_crud
from app.routers.user import get_current_user   # ✅ JWT dependency

router = APIRouter()

# ✅ Load AWS credentials
load_dotenv()
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
bucket = os.getenv("AWS_BUCKET_NAME")

# -------------------------------------------------------------------------
# 🔐 Upload file (authenticated)
# -------------------------------------------------------------------------
@router.post("/files/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    message_id: str | None = None,
    current_user_id: str = Depends(get_current_user)    # ✅ require valid token
):
    """Upload a file to S3 and create its metadata in Neo4j. Requires authentication."""
    file_id = str(uuid4())
    object_name = f"{file_id}_{file.filename}"

    # ✅ calculate file size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    try:
        s3.upload_fileobj(file.file, bucket, object_name,
                          ExtraArgs={"ContentType": file.content_type})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload to S3 failed: {str(e)}")

    file_url = f"https://{bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{object_name}"

    # ✅ Create the file metadata node
    file_node = file_crud.attach_file(
        file_id=file_id,
        url=file_url,
        file_type=file.content_type or "application/octet-stream",
        size=file_size,
        message_id=message_id
    )

    if not file_node and message_id:
        raise HTTPException(status_code=404, detail="Message not found to attach file")

    return FileResponse(
        file_id=file_id,
        url=file_url,
        file_type=file.content_type or "application/octet-stream",
        size=file_size,
    )

# -------------------------------------------------------------------------
# 🔐 Update file (authenticated)
# -------------------------------------------------------------------------
@router.put("/files/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: str,
    file: UploadFile = File(..., description="The new file to replace the old one"),
    current_user_id: str = Depends(get_current_user)    # ✅ enforce valid token
):
    """
    Replace an existing file with a new upload.
    - Uploads the new file to S3 (overwriting the old object key)
    - Updates the file's metadata (URL, type, size) in the database
    """
    # locate the existing file node
    existing_file = file_crud.get_file_by_id(file_id)
    if not existing_file:
        raise HTTPException(status_code=404, detail="File not found")

    # you could add an ownership check here if File nodes are linked to users

    # compute new size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    # keep the same object key structure (overwrite in S3)
    object_name = f"{file_id}_{file.filename}"

    try:
        s3.upload_fileobj(
            file.file,
            bucket,
            object_name,
            ExtraArgs={"ContentType": file.content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")

    # construct new URL
    file_url = f"https://{bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{object_name}"

    # update metadata in Neo4j
    updated_file = file_crud.update_file(
        file_id,
        url=file_url,
        file_type=file.content_type or "application/octet-stream",
        size=file_size,
    )
    if not updated_file:
        raise HTTPException(status_code=404, detail="Failed to update file metadata")

    return FileResponse(
        file_id=updated_file.file_id,
        url=updated_file.url,
        file_type=updated_file.file_type,
        size=updated_file.size,
    )

# -------------------------------------------------------------------------
# 🔐 Delete file (authenticated)
# -------------------------------------------------------------------------
@router.delete("/files/{file_id}", status_code=status.HTTP_200_OK)
def delete_file(
    file_id: str,
    current_user_id: str = Depends(get_current_user)    # ✅ require valid token
):
    """Delete a file by ID. Requires authentication."""
    success = file_crud.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    return {"detail": "File deleted successfully"}