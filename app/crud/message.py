from uuid import uuid4
from datetime import datetime

from app.config import neo4j_conn
from app.models import Message, User, Conversation, File   # ✅ import File as well


class MessageCRUD:
    def __init__(self, connection):
        self.connection = connection

    def send_message(self, sender_id: str, conversation_id: str,
                     content: str, file_ids: list[str] | None = None) -> Message | None:
        """Create a message, link it to sender + conversation, and optionally attach files."""

        # Fetch sender and conversation nodes
        sender = User.nodes.get_or_none(user_id=sender_id)
        conversation = Conversation.nodes.get_or_none(conversation_id=conversation_id)

        if not sender or not conversation:
            return None

        # Fetch file nodes if provided
        file_nodes = []
        if file_ids:
            for fid in file_ids:
                f = File.nodes.get_or_none(file_id=fid)
                if f:
                    file_nodes.append(f)

        # Use the helper on Message model
        msg = Message.create_with_files(
            message_id=str(uuid4()),
            content=content,
            sender_node=sender,
            conversation_node=conversation,
            file_nodes=file_nodes
        )

        return msg

    def get_messages_in_conversation(self, conversation_id: str) -> list[Message]:
        """Retrieve all messages in a conversation, ordered by timestamp."""
        conversation = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not conversation:
            return []
        return list(conversation.messages.order_by("timestamp"))

    def update_message(self, message_id: str, new_content: str) -> Message | None:
        """Update a message’s content."""
        message = Message.nodes.get_or_none(message_id=message_id)
        if not message:
            return None
        message.content = new_content
        message.save()
        return message

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID."""
        message = Message.nodes.get_or_none(message_id=message_id)
        if not message:
            return False
        message.delete()
        return True


# ✅ Instantiate the CRUD class
message_crud = MessageCRUD(neo4j_conn)