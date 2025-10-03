from fastapi import APIRouter, HTTPException, status, UploadFile, File
from uuid import uuid4
import boto3, os
from dotenv import load_dotenv
from app.schemas.file import FileResponse, FileUpdate
from app.crud.file import file_crud

router = APIRouter()

# ✅ Load .env to bring in AWS credentials
load_dotenv()

# ✅ Initialize boto3 S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
bucket = os.getenv("AWS_BUCKET_NAME")


@router.post("/files/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), message_id: str | None = None):
    """Upload a real file to S3 and create metadata in Neo4j."""
    file_id = str(uuid4())
    object_name = f"{file_id}_{file.filename}"

    # ✅ calculate size first (before upload)
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)   # reset pointer to start

    try:
        # upload file object to S3
        s3.upload_fileobj(file.file, bucket, object_name,
                          ExtraArgs={"ContentType": file.content_type})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload to S3 failed: {str(e)}")

    # Construct file URL
    file_url = f"https://{bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{object_name}"

    # Create Neo4j File node
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
        size=file_size
    )

@router.put("/files/{file_id}", response_model=FileResponse)
def update_file(file_id: str, file_update: FileUpdate):
    """Update an existing file by ID."""
    updated_file = file_crud.update_file(file_id, **file_update.dict())
    if not updated_file:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_id=updated_file.file_id,
        url=updated_file.url,
        file_type=updated_file.file_type,
        size=updated_file.size,
    )


@router.delete("/files/{file_id}", status_code=status.HTTP_200_OK)
def delete_file(file_id: str):
    """Delete a file by ID."""
    success = file_crud.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    return {"detail": "File deleted successfully"}