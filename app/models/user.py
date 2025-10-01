from neomodel import StructuredNode, StringProperty, RelationshipTo

class User(StructuredNode):
    user_id = StringProperty(unique_index=True, required=True)
    username = StringProperty(unique_index=True, required=True)
    email = StringProperty(unique_index=True, required=True)
    password_hash = StringProperty(required=True)

    sent_messages = RelationshipTo("app.models.message.Message", "SENT")
    member_of = RelationshipTo("app.models.conversation.Conversation", "MEMBER_OF")