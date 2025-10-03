from neomodel import StructuredNode, StringProperty, DateTimeProperty, UniqueIdProperty, RelationshipFrom, RelationshipTo
from datetime import datetime

class Reaction(StructuredNode):
    uid = UniqueIdProperty()
    reaction_id = StringProperty(unique_index=True, required=True)
    type = StringProperty(
        required=True,
        choices={
            "like": "Like",
            "haha": "Haha",
            "sad": "Sad",
            "angry": "Angry",
            "care": "Care"
        }
    )
    created_at = DateTimeProperty(default_now=True)

    # Relationships
    user = RelationshipFrom("app.models.user.User", "REACTED")
    post = RelationshipTo("app.models.post.Post", "ON_POST")