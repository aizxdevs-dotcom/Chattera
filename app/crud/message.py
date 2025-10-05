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
        file_ids: Optional[List[str]] = None
    ) -> Optional[Message]:
        """
        Create a message, link it to sender + conversation,
        and optionally attach uploaded files.
        A message may contain only text, only files, or both.
        """

        # --- Fetch sender & conversation ---
        sender = User.nodes.get_or_none(user_id=sender_id)
        conversation = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not sender or not conversation:
            return None

        # --- Fetch file nodes if any provided ---
        file_nodes: list[File] = []
        if file_ids:
            for fid in file_ids:
                file_node = File.nodes.get_or_none(file_id=fid)
                if file_node:
                    file_nodes.append(file_node)

        # --- Create message node ---
        msg = Message.create_with_files(
            message_id=str(uuid4()),
            content=content or "",          # ✅ allow empty content for file‑only message
            sender_node=sender,
            conversation_node=conversation,
            file_nodes=file_nodes,
        )
        return msg

    # ------------------------------------------------------------------
    # 💬  Retrieve messages for conversation
    # ------------------------------------------------------------------
    def get_messages_in_conversation(self, conversation_id: str) -> List[Message]:
        """
        Retrieve all messages in a conversation ordered by timestamp (oldest first).
        Returns an empty list if conversation not found.
        """
        conversation = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not conversation:
            return []
        return list(conversation.messages.order_by("timestamp"))

    # ------------------------------------------------------------------
    # ✏️  Update existing message text
    # ------------------------------------------------------------------
    def update_message(self, message_id: str, new_content: str) -> Optional[Message]:
        """Update message content (text)."""
        message = Message.nodes.get_or_none(message_id=message_id)
        if not message:
            return None
        message.content = new_content
        message.timestamp = datetime.utcnow()  # optional: refresh timestamp
        message.save()
        return message

    # ------------------------------------------------------------------
    # ❌  Delete message
    # ------------------------------------------------------------------
    def delete_message(self, message_id: str) -> bool:
        """Delete a message by its unique ID."""
        message = Message.nodes.get_or_none(message_id=message_id)
        if not message:
            return False
        message.delete()
        return True


# ✅  Instantiate singleton CRUD object
message_crud = MessageCRUD(neo4j_conn)