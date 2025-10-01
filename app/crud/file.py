from app.config import neo4j_conn
from app.models import File, Message


class FileCRUD:
    def __init__(self, connection):
        self.connection = connection

    def attach_file(self, file_id, url, file_type, size, message_id) -> File | None:
        """Create a File node and attach it to a Message."""
        # Ensure the message exists
        message = Message.nodes.get_or_none(message_id=message_id)
        if not message:
            return None

        # Create and save the file
        file_node = File(
            file_id=file_id,
            url=url,
            file_type=file_type,
            size=size,
        ).save()

        # ✅ connect it to the message
        message.attachments.connect(file_node)

        return file_node

    def update_file(self, file_id: str, url: str = None, file_type: str = None, size: int = None) -> File | None:
        """Update file properties (partial update)."""
        file_node = File.nodes.get_or_none(file_id=file_id)
        if not file_node:
            return None

        if url is not None:
            file_node.url = url
        if file_type is not None:
            file_node.file_type = file_type
        if size is not None:
            file_node.size = size

        file_node.save()
        return file_node

    def delete_file(self, file_id: str) -> bool:
        """Delete a file node."""
        file_node = File.nodes.get_or_none(file_id=file_id)
        if not file_node:
            return False

        file_node.delete()  # This also removes relationships
        return True


# ✅ instantiate the CRUD
file_crud = FileCRUD(neo4j_conn)