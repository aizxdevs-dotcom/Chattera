from app.models.user import User

def list_contacts(user_uid: str):
    user = User.nodes.get(uid=user_uid)
    return [{"user_uid": user.uid, "contact_uid": c.uid} for c in user.contacts.all()]