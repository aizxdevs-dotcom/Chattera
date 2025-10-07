from neomodel import (
    StructuredNode, StringProperty, DateTimeProperty, BooleanProperty,
    RelationshipTo,
)
from datetime import datetime
from app.models.user import User
from app.models.post import Post


class Notification(StructuredNode):
    notification_id = StringProperty(unique_index=True, required=True)
    receiver_id = StringProperty(required=True)   # User to notify
    sender_id = StringProperty(required=True)     # Actor of the event
    post_id = StringProperty(required=True)
    type = StringProperty(
    required=True,
    choices=[("like", "like"), ("comment", "comment")]
)
    message = StringProperty()
    created_at = DateTimeProperty(default_now=True)
    is_read = BooleanProperty(default=False)

    sender = RelationshipTo(User, "SENT_BY")
    post = RelationshipTo(Post, "ABOUT")