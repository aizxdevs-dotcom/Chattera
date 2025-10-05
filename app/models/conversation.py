from neomodel import StructuredNode, StringProperty, BooleanProperty, RelationshipFrom, RelationshipTo

class Conversation(StructuredNode):
    """A message thread or group chat."""
    conversation_id = StringProperty(unique_index=True, required=True)
    is_group = BooleanProperty(required=True)

    # Users that are part of this conversation
    members = RelationshipFrom("app.models.user.User", "MEMBER_OF")

    # Messages linked to this conversation
    messages = RelationshipFrom("app.models.message.Message", "IN_CONVERSATION")