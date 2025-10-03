from neomodel import StructuredNode, StringProperty, DateTimeProperty, UniqueIdProperty, RelationshipFrom, RelationshipTo
import datetime

class Post(StructuredNode):
    uid = UniqueIdProperty()
    post_id = StringProperty(unique_index=True, required=True)
    description = StringProperty(required=False)  # 🆕 description text
    created_at = DateTimeProperty(default_now=True)

    # Relationships
    author = RelationshipFrom("app.models.user.User", "AUTHORED")
    attachments = RelationshipTo("app.models.file.File", "POST_HAS_ATTACHMENT")  # 🆕 attach multiple files
    reactions = RelationshipFrom("app.models.reaction.Reaction", "ON_POST")  # all reactions on this post
    comments = RelationshipFrom("app.models.comment.Comment", "ON_POST") 