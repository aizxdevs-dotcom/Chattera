from uuid import uuid4
from typing import Optional
from datetime import datetime

from app.config import neo4j_conn
from app.models import File, Message


class FileCRUD:
    """CRUD operations for File nodes, with optional message attachment."""

    def __init__(self, connection):
        self.connection = connection

    # -------------------------------------------------------------
    # 🔹 Create a standalone File node
    # -------------------------------------------------------------
    def create_file(
        self,
        file_url: str,
        file_type: str,
        size: int,
    ) -> File:
        """
        Create a file node without attaching to a message.
        Used when generic uploads happen (e.g. message or comment builds link later).
        """
        file_node = File(
            file_id=str(uuid4()),
            url=file_url,
            file_type=file_type,
            size=size,
        ).save()
        return file_node

    # -------------------------------------------------------------
    # 🔹 Create / attach file (for upload that references message_id)
    # -------------------------------------------------------------
    def attach_file(
        self,
        file_id: str,
        url: str,
        file_type: str,
        size: int,
        message_id: Optional[str] = None,
    ) -> Optional[File]:
        """
        Create a new File node (optionally attach to a Message).
        If message_id is provided, attach to that message after saving.
        """
        file_node = File(
            file_id=file_id,
            url=url,
            file_type=file_type,
            size=size,
        ).save()

        if message_id:
            message = Message.nodes.get_or_none(message_id=message_id)
            if not message:
                # Remove dangling file node if attach target missing
                file_node.delete()
                return None
            message.attachments.connect(file_node)

        return file_node

    # -------------------------------------------------------------
    # 🔹 Retrieve file by ID
    # -------------------------------------------------------------
    def get_file_by_id(self, file_id: str) -> Optional[File]:
        """Fetch a File node by its unique ID."""
        return File.nodes.get_or_none(file_id=file_id)

    # -------------------------------------------------------------
    # 🔹 Update
    # -------------------------------------------------------------
    def update_file(self, file_id: str, **kwargs) -> Optional[File]:
        """Update file properties (partial)."""
        file_node = File.nodes.get_or_none(file_id=file_id)
        if not file_node:
            return None

        for field, value in kwargs.items():
            if hasattr(file_node, field) and value is not None:
                setattr(file_node, field, value)

        file_node.save()
        return file_node

    # -------------------------------------------------------------
    # 🔹 Delete
    # -------------------------------------------------------------
    def delete_file(self, file_id: str) -> bool:
        """Delete a file node and disconnect relationships."""
        file_node = File.nodes.get_or_none(file_id=file_id)
        if not file_node:
            return False

        file_node.delete()
        return True


# ✅ Singleton CRUD instance
file_crud = FileCRUD(neo4j_conn)