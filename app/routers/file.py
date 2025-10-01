from fastapi import APIRouter, HTTPException
from uuid import uuid4

from app.schemas.file import FileCreate, FileResponse
from app.crud.file import file_crud   # ✅ import the CRUD object, not a missing function

router = APIRouter()


@router.post("/files", response_model=FileResponse)
def attach_new_file(file: FileCreate):
    """Attach a new file to a message."""
    file_id = str(uuid4())
    created_file = file_crud.attach_file(file_id, file.url, file.file_type, file.size, file.message_id)

    if not created_file:
        raise HTTPException(status_code=404, detail="Message not found to attach file")

    return FileResponse(
        file_id=created_file.file_id,
        url=created_file.url,
        file_type=created_file.file_type,
        size=created_file.size,
    )


@router.put("/files/{file_id}", response_model=FileResponse)
def update_file(file_id: str, file_update: FileCreate):
    """Update an existing file by ID."""
    updated_file = file_crud.update_file(
        file_id=file_id,
        url=file_update.url,
        file_type=file_update.file_type,
        size=file_update.size
    )
    if not updated_file:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_id=updated_file.file_id,
        url=updated_file.url,
        file_type=updated_file.file_type,
        size=updated_file.size,
    )


@router.delete("/files/{file_id}")
def delete_file(file_id: str):
    """Delete a file by ID."""
    success = file_crud.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    return {"detail": "File deleted successfully"}