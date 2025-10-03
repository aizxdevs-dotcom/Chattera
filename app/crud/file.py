from app.config import neo4j_conn
from app.models import File, Message


class FileCRUD:
    def __init__(self, connection):
        self.connection = connection

    def attach_file(self, file_id: str, url: str, file_type: str, size: int, message_id: str | None = None) -> File | None:
        """Create a File node and optionally attach it to a Message."""
        # Always create the File node
        file_node = File(
            file_id=file_id,
            url=url,
            file_type=file_type,
            size=size,
        ).save()

        # If message_id provided, attempt to connect
        if message_id:
            message = Message.nodes.get_or_none(message_id=message_id)
            if not message:
                # If no message found, return None to indicate a bad request
                return None
            message.attachments.connect(file_node)

        return file_node

    def update_file(self, file_id: str, **kwargs) -> File | None:
        """Update file properties (partial update)."""
        file_node = File.nodes.get_or_none(file_id=file_id)
        if not file_node:
            return None

        for field, value in kwargs.items():
            if value is not None and hasattr(file_node, field):
                setattr(file_node, field, value)

        file_node.save()
        return file_node

    def delete_file(self, file_id: str) -> bool:
        """Delete a file node and its relationships."""
        file_node = File.nodes.get_or_none(file_id=file_id)
        if not file_node:
            return False

        file_node.delete()  # This also removes all connected relationships
        return True


# ✅ instantiate the CRUD
file_crud = FileCRUD(neo4j_conn)