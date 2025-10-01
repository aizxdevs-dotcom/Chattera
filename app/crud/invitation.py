from app.models.user import User

def send_invitation(sender_uid: str, receiver_uid: str):
    sender = User.nodes.get(uid=sender_uid)
    receiver = User.nodes.get(uid=receiver_uid)
    existing = sender.sent_invitations.relationship(receiver)
    if existing:
        return existing
    rel = sender.sent_invitations.connect(receiver, {'status': 'pending'})
    return rel

def respond_invitation(sender_uid: str, receiver_uid: str, accept: bool):
    sender = User.nodes.get(uid=sender_uid)
    receiver = User.nodes.get(uid=receiver_uid)
    rel = sender.sent_invitations.relationship(receiver)
    if not rel:
        return None
    rel.status = "accepted" if accept else "declined"
    rel.save()
    if accept:
        sender.contacts.connect(receiver)
        receiver.contacts.connect(sender)
    return rel

def list_invitations(user_uid: str):
    user = User.nodes.get(uid=user_uid)
    pending = []
    for inviter in user.received_invitations.match(status="pending"):
        rel = inviter.sent_invitations.relationship(user)
        pending.append({
            "sender_uid": inviter.uid,
            "receiver_uid": user.uid,
            "status": rel.status
        })
    return pending