from app.models.user import User
from neomodel.exceptions import DoesNotExist
from datetime import datetime
from typing import Optional, Dict, List

def send_invitation(sender_uid: str, receiver_uid: str, message: Optional[str] = None):
    """Send a friend request"""
    try:
        sender = User.nodes.get(uid=sender_uid)
        receiver = User.nodes.get(uid=receiver_uid)
    except DoesNotExist:
        return None
    
    # Check if already friends
    if sender.contacts.is_connected(receiver):
        return {"error": "already_friends"}
    
    # Check if invitation already exists
    existing = sender.sent_invitations.relationship(receiver)
    if existing:
        return {"error": "invitation_exists", "status": existing.status}
    
    # Check reverse invitation
    reverse = receiver.sent_invitations.relationship(sender)
    if reverse:
        return {"error": "reverse_invitation_exists", "status": reverse.status}
    
    # Create new invitation
    rel = sender.sent_invitations.connect(receiver, {
        'status': 'pending',
        'message': message or '',
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })
    return rel

def respond_invitation(sender_uid: str, receiver_uid: str, accept: bool):
    """Accept or decline a friend request"""
    try:
        sender = User.nodes.get(uid=sender_uid)
        receiver = User.nodes.get(uid=receiver_uid)
    except DoesNotExist:
        return None
    
    rel = sender.sent_invitations.relationship(receiver)
    if not rel:
        return None
    
    if rel.status != "pending":
        return {"error": "already_responded", "status": rel.status}
    
    rel.status = "accepted" if accept else "declined"
    rel.updated_at = datetime.now()
    rel.save()
    
    # If accepted, create bidirectional friendship
    if accept:
        if not sender.contacts.is_connected(receiver):
            sender.contacts.connect(receiver, {'created_at': datetime.now()})
        if not receiver.contacts.is_connected(sender):
            receiver.contacts.connect(sender, {'created_at': datetime.now()})
    
    return rel

def cancel_invitation(sender_uid: str, receiver_uid: str):
    """Cancel a sent friend request"""
    try:
        sender = User.nodes.get(uid=sender_uid)
        receiver = User.nodes.get(uid=receiver_uid)
    except DoesNotExist:
        return False
    
    rel = sender.sent_invitations.relationship(receiver)
    if not rel or rel.status != "pending":
        return False
    
    sender.sent_invitations.disconnect(receiver)
    return True

def list_received_invitations(user_uid: str, status_filter: Optional[str] = "pending"):
    """Get friend requests received by user"""
    try:
        user = User.nodes.get(uid=user_uid)
    except DoesNotExist:
        return []
    
    pending = []
    query = user.received_invitations.match(status=status_filter) if status_filter else user.received_invitations.all()
    
    for inviter in query:
        rel = inviter.sent_invitations.relationship(user)
        pending.append({
            "sender_uid": inviter.uid,
            "receiver_uid": user.uid,
            "sender_username": inviter.username,
            "sender_profile_photo": inviter.profile_photo,
            "status": rel.status,
            "message": rel.message if hasattr(rel, 'message') else None,
            "created_at": rel.created_at.isoformat() if hasattr(rel, 'created_at') else None,
            "sender": inviter
        })
    return pending

def list_sent_invitations(user_uid: str, status_filter: Optional[str] = "pending"):
    """Get friend requests sent by user"""
    try:
        user = User.nodes.get(uid=user_uid)
    except DoesNotExist:
        return []
    
    sent = []
    query = user.sent_invitations.match(status=status_filter) if status_filter else user.sent_invitations.all()
    
    for receiver in query:
        rel = user.sent_invitations.relationship(receiver)
        sent.append({
            "sender_uid": user.uid,
            "receiver_uid": receiver.uid,
            "receiver_username": receiver.username,
            "receiver_profile_photo": receiver.profile_photo,
            "status": rel.status,
            "message": rel.message if hasattr(rel, 'message') else None,
            "created_at": rel.created_at.isoformat() if hasattr(rel, 'created_at') else None,
            "receiver": receiver
        })
    return sent

def count_pending_received(user_uid: str) -> int:
    """Count pending friend requests received"""
    try:
        user = User.nodes.get(uid=user_uid)
        return len(user.received_invitations.match(status="pending"))
    except DoesNotExist:
        return 0

def count_pending_sent(user_uid: str) -> int:
    """Count pending friend requests sent"""
    try:
        user = User.nodes.get(uid=user_uid)
        return len(user.sent_invitations.match(status="pending"))
    except DoesNotExist:
        return 0