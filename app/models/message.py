from neomodel import (
    StructuredNode, StringProperty, DateTimeProperty,
    RelationshipTo, RelationshipFrom
)
from datetime import datetime

class Message(StructuredNode):
    message_id = StringProperty(unique_index=True, required=True)
    content = StringProperty(required=True)
    timestamp = DateTimeProperty(default_now=True)

    # Relationships
    sender = RelationshipFrom("app.models.user.User", "SENT")
    in_conversation = RelationshipTo("app.models.conversation.Conversation", "IN_CONVERSATION")
    attachments = RelationshipTo("app.models.file.File", "ATTACHED_TO")

    @classmethod
    def create_with_files(cls, message_id: str, content: str,
                          sender_node, conversation_node,
                          file_nodes: list = None):
        """
        Convenience constructor: create a message and wire up sender, conversation, and files.
        - sender_node: a User node (app.models.user.User)
        - conversation_node: a Conversation node (app.models.conversation.Conversation)
        - file_nodes: a list of File nodes (app.models.file.File)
        """
        # Create message
        msg = cls(message_id=message_id, content=content, timestamp=datetime.utcnow()).save()

        # Connect sender
        if sender_node:
            sender_node.sent_messages.connect(msg)

        # Connect conversation
        if conversation_node:
            msg.in_conversation.connect(conversation_node)

        # Attach files if provided
        if file_nodes:
            for f in file_nodes:
                msg.attachments.connect(f)

        return msg