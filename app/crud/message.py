from uuid import uuid4
from datetime import datetime
from typing import List, Optional

from app.config import neo4j_conn
from app.models import Message, User, Conversation, File


class MessageCRUD:
    def __init__(self, connection):
        self.connection = connection

    # ------------------------------------------------------------------
    # 📨  Create / send a new message
    # ------------------------------------------------------------------
    def send_message(
        self,
        sender_id: str,
        conversation_id: str,
        content: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
    ) -> Optional[Message]:
        """Create a message and attach any provided files."""
        sender = User.nodes.get_or_none(user_id=sender_id)
        conversation = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not sender or not conversation:
            return None

        file_nodes: list[File] = []
        if file_ids:
            for fid in file_ids:
                file_node = File.nodes.get_or_none(file_id=fid)
                if file_node:
                    file_nodes.append(file_node)

        msg = Message.create_with_files(
            message_id=str(uuid4()),
            content=content or "",
            sender_node=sender,
            conversation_node=conversation,
            file_nodes=file_nodes,
        )
        return msg

    # ------------------------------------------------------------------
    # 💬  Retrieve messages for conversation
    # ------------------------------------------------------------------
    def get_messages_in_conversation(self, conversation_id: str) -> List[Message]:
        """Return all messages in a conversation ordered by timestamp."""
        conversation = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not conversation:
            return []
        return list(conversation.messages.order_by("timestamp"))

    # ------------------------------------------------------------------
    # 🔍  Get single message by ID
    # ------------------------------------------------------------------
    def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Fetch a single message node by ID."""
        return Message.nodes.get_or_none(message_id=message_id)

    # ------------------------------------------------------------------
    # ✏️  Update existing message (text and/or files)
    # ------------------------------------------------------------------
    def update_message(
        self,
        message_id: str,
        new_content: Optional[str] = None,
        new_file_ids: Optional[List[str]] = None,
    ) -> Optional[Message]:
        """Update message content and/or attached files."""
        message = self.get_message_by_id(message_id)
        if not message:
            return None

        if new_content is not None:
            message.content = new_content

        if new_file_ids is not None:
            # Clear existing attachments
            for f in list(message.attachments):
                message.attachments.disconnect(f)
            # Re‑connect new files
            for fid in new_file_ids:
                file_node = File.nodes.get_or_none(file_id=fid)
                if file_node:
                    message.attachments.connect(file_node)

        message.timestamp = datetime.utcnow()
        message.save()
        return message

    # ------------------------------------------------------------------
    # ❌  Delete message (flexible)
    # ------------------------------------------------------------------
    def delete_message(
        self,
        message_id: str,
        delete_content: bool = True,
        delete_files: bool = True,
    ) -> Optional[Message]:
        """
        Delete specific parts of a message.
          - delete_content=False → keep text
          - delete_files=False → keep attachments
        Delete node entirely if both True.
        """
        message = self.get_message_by_id(message_id)
        if not message:
            return None

        if delete_content and delete_files:
            message.delete()
            return None

        if delete_content:
            message.content = ""

        if delete_files:
            for f in list(message.attachments):
                message.attachments.disconnect(f)

        message.timestamp = datetime.utcnow()
        message.save()
        return message

# ✅  Instantiate singleton CRUD object
message_crud = MessageCRUD(neo4j_conn)