from neomodel import StructuredNode, StringProperty, RelationshipTo, RelationshipFrom, StructuredRel, UniqueIdProperty 

class InvitationRel(StructuredRel):
    # Relationship properties let us track status changes
    status = StringProperty(default="pending")  # pending | accepted | declined
class User(StructuredNode):
    uid = UniqueIdProperty() 
    user_id = StringProperty(unique_index=True, required=True)
    username = StringProperty(unique_index=True, required=True)
    email = StringProperty(unique_index=True, required=True)
    password_hash = StringProperty(required=True)

    full_name = StringProperty(required=False)
    bio = StringProperty(required=False)
    profile_photo = StringProperty(required=False) 

    sent_messages = RelationshipTo("app.models.message.Message", "SENT")
    member_of = RelationshipTo("app.models.conversation.Conversation", "MEMBER_OF")

    sent_invitations = RelationshipTo("User", "INVITED", model=InvitationRel)
    received_invitations = RelationshipFrom("User", "INVITED", model=InvitationRel)

    contacts = RelationshipTo("User", "CONTACT")
    authored = RelationshipTo("app.models.post.Post", "AUTHORED")
    reactions = RelationshipTo("app.models.reaction.Reaction", "REACTED")  # user → reaction
    comments = RelationshipTo("app.models.comment.Comment", "COMMENTED")   # user → comment