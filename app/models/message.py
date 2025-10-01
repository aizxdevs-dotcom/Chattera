from neomodel import StructuredNode, StringProperty, DateTimeProperty, RelationshipFrom, RelationshipTo

class Message(StructuredNode):
    message_id = StringProperty(unique_index=True, required=True)
    content = StringProperty(required=True)
    timestamp = DateTimeProperty(required=True)

    sender = RelationshipFrom("app.models.user.User", "SENT")
    in_conversation = RelationshipTo("app.models.conversation.Conversation", "IN_CONVERSATION")
    attachments = RelationshipFrom("app.models.file.File", "ATTACHED_TO")