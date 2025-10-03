from neomodel import StructuredNode, StringProperty, DateTimeProperty, UniqueIdProperty, RelationshipFrom, RelationshipTo
from datetime import datetime

class Comment(StructuredNode):
    uid = UniqueIdProperty()
    comment_id = StringProperty(unique_index=True, required=True)
    description = StringProperty(required=False) 
    created_at = DateTimeProperty(default_now=True)

    # Relationships
    user = RelationshipFrom("app.models.user.User", "COMMENTED")
    post = RelationshipTo("app.models.post.Post", "ON_POST")
    attachments = RelationshipTo("app.models.file.File", "COMMENT_HAS_ATTACHMENT") 
    reactions = RelationshipFrom("app.models.reaction.Reaction", "ON_COMMENT")