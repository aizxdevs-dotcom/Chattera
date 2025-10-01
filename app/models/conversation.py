from neomodel import StructuredNode, StringProperty, BooleanProperty, RelationshipFrom
from app.models.message import Message  # only if needed directly, or string ref

class Conversation(StructuredNode):
    conversation_id = StringProperty(unique_index=True, required=True)
    is_group = BooleanProperty(required=True)

    # Relationship from User to Conversation
    members = RelationshipFrom("app.models.user.User", "MEMBER_OF")

    # 👇 Add this: Relationship from Message → Conversation
    messages = RelationshipFrom("app.models.message.Message", "IN_CONVERSATION")