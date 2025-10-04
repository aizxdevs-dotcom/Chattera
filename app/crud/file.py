from app.config import neo4j_conn
from app.models import File, Message


class FileCRUD:
    def __init__(self, connection):
        self.connection = connection

    # -------------------------------------------------------------
    # 🔹 Create / attach file
    # -------------------------------------------------------------
    def attach_file(
        self,
        file_id: str,
        url: str,
        file_type: str,
        size: int,
        message_id: str | None = None
    ) -> File | None:
        """Create a File node and optionally attach it to a Message."""
        file_node = File(
            file_id=file_id,
            url=url,
            file_type=file_type,
            size=size,
        ).save()

        if message_id:
            message = Message.nodes.get_or_none(message_id=message_id)
            if not message:
                return None
            message.attachments.connect(file_node)

        return file_node

    # -------------------------------------------------------------
    # 🔹 Retrieve file by ID
    # -------------------------------------------------------------
    def get_file_by_id(self, file_id: str) -> File | None:
        """Fetch a File node by its unique ID."""
        return File.nodes.get_or_none(file_id=file_id)

    # -------------------------------------------------------------
    # 🔹 Update
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # 🔹 Delete
    # -------------------------------------------------------------
    def delete_file(self, file_id: str) -> bool:
        """Delete a file node and its relationships."""
        file_node = File.nodes.get_or_none(file_id=file_id)
        if not file_node:
            return False

        file_node.delete()  # removes connected relationships as well
        return True


# ✅ instantiate the CRUD
file_crud = FileCRUD(neo4j_conn)