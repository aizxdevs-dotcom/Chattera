from neomodel import (
    StructuredNode, StringProperty, RelationshipTo, 
    RelationshipFrom, StructuredRel, UniqueIdProperty, DateTimeProperty
)
from datetime import datetime

class InvitationRel(StructuredRel):
    # Relationship properties let us track status changes
    status = StringProperty(default="pending")  # pending | accepted | declined
    message = StringProperty(default="")  # Optional message with friend request
    created_at = DateTimeProperty(default=lambda: datetime.now())
    updated_at = DateTimeProperty(default=lambda: datetime.now())

class ContactRel(StructuredRel):
    # Track when friendship was established
    created_at = DateTimeProperty(default=lambda: datetime.now())
class User(StructuredNode):
    uid = UniqueIdProperty() 
    user_id = StringProperty(unique_index=True, required=True)
    username = StringProperty(unique_index=True, required=True)
    email = StringProperty(unique_index=True, required=True)
    password_hash = StringProperty(required=True)

    full_name = StringProperty(required=False)
    bio = StringProperty(required=False)
    profile_photo = StringProperty(required=False) 

    # Email verification fields
    is_verified = StringProperty(default="false")  # "true" or "false" as string
    otp_code = StringProperty(required=False)  # 4-digit OTP
    otp_expires_at = DateTimeProperty(required=False)  # OTP expiry timestamp
    
    # Password reset fields
    reset_token = StringProperty(required=False)  # Reset OTP code
    reset_token_expires_at = DateTimeProperty(required=False)  # Reset token expiry

    sent_messages = RelationshipTo("app.models.message.Message", "SENT")
    member_of = RelationshipTo("app.models.conversation.Conversation", "MEMBER_OF")

    sent_invitations = RelationshipTo("User", "INVITED", model=InvitationRel)
    received_invitations = RelationshipFrom("User", "INVITED", model=InvitationRel)

    contacts = RelationshipTo("User", "CONTACT", model=ContactRel)
    authored = RelationshipTo("app.models.post.Post", "AUTHORED")
    reactions = RelationshipTo("app.models.reaction.Reaction", "REACTED")  # user → reaction
    comments = RelationshipTo("app.models.comment.Comment", "COMMENTED")   # user → comment