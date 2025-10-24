from app.config import neo4j_conn
from app.schemas.user import UserResponse
from app.models.user import User
from neomodel.exceptions import DoesNotExist
from app.models import User, Conversation, Message
from app.schemas.user import UserResponse

class UserCRUD:
    def __init__(self, connection):
        self.connection = connection

    def create_user(self, user_id, username, email, password_hash, otp_code=None, otp_expires_at=None):
        if User.nodes.filter(email=email):
            raise ValueError("Email already registered")

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            is_verified="false",
            otp_code=otp_code,
            otp_expires_at=otp_expires_at
        ).save()

        return user

    def get_user_by_email(self, email):
        try:
            return User.nodes.get(email=email)
        except DoesNotExist:
            return None

    def get_user_by_id(self, user_id):
        try:
            return User.nodes.get(user_id=user_id)
        except DoesNotExist:
            return None
    
    def update_user(self, user_id: str, full_name=None, bio=None, profile_photo=None):
        user = User.nodes.get_or_none(user_id=user_id)
        if not user:
            return None

        if full_name is not None:
            user.full_name = full_name
        if bio is not None:
            user.bio = bio
        if profile_photo is not None:
            user.profile_photo = profile_photo

        user.save()
        return user
    
    def get_all_users(self, exclude_user_id: str = None, limit: int = 50):
        """
        Get all users in the system for 'People You May Know'.
        Excludes the current user if exclude_user_id is provided.
        """
        cypher_query = """
        MATCH (u:User)
        WHERE u.user_id <> $exclude_id
        RETURN u.user_id AS user_id, u.username AS username, 
               u.full_name AS full_name, u.profile_photo AS profile_photo, 
               u.bio AS bio, u.email AS email
        ORDER BY u.username
        LIMIT $limit
        """
        
        result = self.connection.query(
            cypher_query,
            parameters={
                "exclude_id": exclude_user_id or "",
                "limit": limit
            }
        )
        
        users = []
        for record in result:
            users.append({
                "user_id": str(record["user_id"]),
                "username": record["username"],
                "full_name": record.get("full_name"),
                "profile_photo": record.get("profile_photo"),
                "bio": record.get("bio"),
                "email": record.get("email")
            })

        # Return plain dicts — let the router convert to Pydantic models
        return users
    
    def search_users(self, query: str, exclude_user_id: str = None, limit: int = 20):
        """
        Search users by username or full name.
        Excludes the current user if exclude_user_id is provided.
        """
        query_lower = query.lower()
        
        cypher_query = """
        MATCH (u:User)
        WHERE (toLower(u.username) CONTAINS $query OR toLower(u.full_name) CONTAINS $query)
        AND u.user_id <> $exclude_id
        RETURN u.user_id AS user_id, u.username AS username, 
               u.full_name AS full_name, u.profile_photo AS profile_photo, 
               u.bio AS bio, u.email AS email
        LIMIT $limit
        """
        
        result = self.connection.query(
            cypher_query,
            parameters={
                "query": query_lower,
                "exclude_id": exclude_user_id or "",
                "limit": limit
            }
        )
        
        users = []
        for record in result:
            users.append({
                "user_id": record["user_id"],
                "username": record["username"],
                "full_name": record.get("full_name"),
                "profile_photo": record.get("profile_photo"),
                "bio": record.get("bio"),
                "email": record.get("email")
            })
        
        return users
    
    def verify_user(self, user_id: str):
        """Mark user as verified and clear OTP"""
        user = User.nodes.get_or_none(user_id=user_id)
        if user:
            user.is_verified = "true"
            user.otp_code = None
            user.otp_expires_at = None
            user.save()
        return user
    
    def update_otp(self, user_id: str, otp_code: str, otp_expires_at):
        """Update user's OTP code and expiry"""
        user = User.nodes.get_or_none(user_id=user_id)
        if user:
            user.otp_code = otp_code
            user.otp_expires_at = otp_expires_at
            user.save()
        return user
    
    def update_reset_token(self, user_id: str, reset_token: str, reset_expires_at):
        """Update user's password reset token and expiry"""
        user = User.nodes.get_or_none(user_id=user_id)
        if user:
            user.reset_token = reset_token
            user.reset_token_expires_at = reset_expires_at
            user.save()
        return user
    
    def reset_user_password(self, user_id: str, new_password_hash: str):
        """Reset user's password and clear reset token"""
        user = User.nodes.get_or_none(user_id=user_id)
        if user:
            user.password_hash = new_password_hash
            user.reset_token = None
            user.reset_token_expires_at = None
            user.save()
        return user
    
    def delete_user(self, user_id: str):
        """Delete user and all their relationships"""
        try:
            user = User.nodes.get_or_none(user_id=user_id)
            if not user:
                return False
            
            # Delete the user node (Neo4j will handle CASCADE relationships)
            user.delete()
            return True
        except Exception as e:
            print(f"Error deleting user {user_id}: {e}")
            return False

# Instantiate the CRUD class
user_crud = UserCRUD(neo4j_conn)