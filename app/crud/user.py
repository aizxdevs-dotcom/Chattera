from app.config import neo4j_conn
from app.models.user import User
from neomodel.exceptions import DoesNotExist
from app.models import User, Conversation, Message

class UserCRUD:
    def __init__(self, connection):
        self.connection = connection

    def create_user(self, user_id, username, email, password_hash):
        if User.nodes.filter(email=email):
            raise ValueError("Email already registered")

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash
        ).save()

        return user

    def get_user_by_email(self, email):
        try:
            return User.nodes.get(email=email)
        except DoesNotExist:
            return None

    def get_user_by_id(self, user_id):
        return User.nodes.get(user_id=user_id)
    
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

# Instantiate the CRUD class
user_crud = UserCRUD(neo4j_conn)