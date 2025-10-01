from app.config import neo4j_conn
from app.models import Message, User, Conversation   # ✅ import only from models package


class MessageCRUD:
    def __init__(self, connection):
        self.connection = connection

    def send_message(self, message_id, content, timestamp, sender_id, conversation_id):
        # Fetch sender and conversation nodes
        sender = User.nodes.get(user_id=sender_id)
        conversation = Conversation.nodes.get(conversation_id=conversation_id)

        # Create and save the message
        message = Message(
            message_id=message_id,
            content=content,
            timestamp=timestamp
        ).save()

        # 🔎 Debug prints — check what classes Python thinks these are
        print("DEBUG >>> Sender class:", sender.__class__)
        print("DEBUG >>> Message class:", message.__class__)
        print("DEBUG >>> Relationship target class:",
              sender.sent_messages.definition["node_class"])

        # Connect relationships
        sender.sent_messages.connect(message)         # User → Message
        message.in_conversation.connect(conversation) # Message → Conversation

        return message

    def get_messages_in_conversation(self, conversation_id):
        conversation = Conversation.nodes.get(conversation_id=conversation_id)
        # Ensure message ordering by timestamp
        return [msg for msg in conversation.messages.order_by("timestamp") if msg]
    
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


# Instantiate the CRUD class
message_crud = MessageCRUD(neo4j_conn)