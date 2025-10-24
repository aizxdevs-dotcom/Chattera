from app.models.user import User
from neomodel.exceptions import DoesNotExist
from typing import List, Dict, Optional

def list_contacts(user_uid: str) -> List[Dict]:
    """Get all friends of a user with full details"""
    try:
        user = User.nodes.get(uid=user_uid)
    except DoesNotExist:
        return []
    
    contacts = []
    for contact in user.contacts.all():
        rel = user.contacts.relationship(contact)
        contacts.append({
            "uid": contact.uid,
            "user_id": contact.user_id,
            "username": contact.username,
            "email": contact.email,
            "full_name": contact.full_name,
            "bio": contact.bio,
            "profile_photo": contact.profile_photo,
            "friendship_since": rel.created_at.isoformat() if hasattr(rel, 'created_at') else None
        })
    return contacts

def get_contact_count(user_uid: str) -> int:
    """Count total friends"""
    try:
        user = User.nodes.get(uid=user_uid)
        return len(user.contacts.all())
    except DoesNotExist:
        return 0

def is_friend(user_uid: str, other_uid: str) -> bool:
    """Check if two users are friends"""
    try:
        user = User.nodes.get(uid=user_uid)
        other = User.nodes.get(uid=other_uid)
        return user.contacts.is_connected(other)
    except DoesNotExist:
        return False

def remove_contact(user_uid: str, contact_uid: str) -> bool:
    """Remove a friend (unfriend) - bidirectional"""
    try:
        user = User.nodes.get(uid=user_uid)
        contact = User.nodes.get(uid=contact_uid)
        
        # Remove bidirectional friendship
        if user.contacts.is_connected(contact):
            user.contacts.disconnect(contact)
        if contact.contacts.is_connected(user):
            contact.contacts.disconnect(user)
        
        return True
    except DoesNotExist:
        return False

def search_contacts(user_uid: str, query: str) -> List[Dict]:
    """Search friends by username or full name"""
    try:
        user = User.nodes.get(uid=user_uid)
    except DoesNotExist:
        return []
    
    query_lower = query.lower()
    contacts = []
    
    for contact in user.contacts.all():
        if (query_lower in contact.username.lower() or 
            (contact.full_name and query_lower in contact.full_name.lower())):
            rel = user.contacts.relationship(contact)
            contacts.append({
                "uid": contact.uid,
                "user_id": contact.user_id,
                "username": contact.username,
                "email": contact.email,
                "full_name": contact.full_name,
                "bio": contact.bio,
                "profile_photo": contact.profile_photo,
                "friendship_since": rel.created_at.isoformat() if hasattr(rel, 'created_at') else None
            })
    
    return contacts

def get_mutual_friends(user_uid: str, other_uid: str) -> List[Dict]:
    """Get mutual friends between two users"""
    try:
        user = User.nodes.get(uid=user_uid)
        other = User.nodes.get(uid=other_uid)
    except DoesNotExist:
        return []
    
    user_contacts = set(c.uid for c in user.contacts.all())
    other_contacts = set(c.uid for c in other.contacts.all())
    mutual_uids = user_contacts.intersection(other_contacts)
    
    mutual_friends = []
    for uid in mutual_uids:
        try:
            mutual = User.nodes.get(uid=uid)
            mutual_friends.append({
                "uid": mutual.uid,
                "user_id": mutual.user_id,
                "username": mutual.username,
                "email": mutual.email,
                "full_name": mutual.full_name,
                "bio": mutual.bio,
                "profile_photo": mutual.profile_photo
            })
        except DoesNotExist:
            continue
    
    return mutual_friends