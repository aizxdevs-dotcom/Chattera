from uuid import uuid4
from typing import List, Optional
from app.config import neo4j_conn
from app.models import Conversation, User


class ConversationCRUD:
    def __init__(self, connection):
        self.connection = connection

    # ------------------------------------------------------------------
    # Create conversation with members
    # ------------------------------------------------------------------
    def create_conversation(
        self,
        is_group: bool,
        member_ids: List[str]
    ) -> Optional[Conversation]:
        """
        Create a new conversation node and connect all given members.
        """
        convo = Conversation(conversation_id=str(uuid4()), is_group=is_group).save()

        for member_id in member_ids:
            user = User.nodes.get_or_none(user_id=member_id)
            if user:
                user.member_of.connect(convo)

        return convo

    # ------------------------------------------------------------------
    # Add / remove members
    # ------------------------------------------------------------------
    def add_member(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        convo = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        user = User.nodes.get_or_none(user_id=user_id)
        if not convo or not user:
            return None
        user.member_of.connect(convo)
        return convo

    def remove_member(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        convo = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        user = User.nodes.get_or_none(user_id=user_id)
        if not convo or not user:
            return None
        user.member_of.disconnect(convo)
        return convo

    # ------------------------------------------------------------------
    # Get / update / delete
    # ------------------------------------------------------------------
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return Conversation.nodes.get_or_none(conversation_id=conversation_id)

    def update_conversation(
        self, conversation_id: str, is_group: Optional[bool] = None
    ) -> Optional[Conversation]:
        convo = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not convo:
            return None
        if is_group is not None:
            convo.is_group = is_group
        convo.save()
        return convo

    def delete_conversation(self, conversation_id: str) -> bool:
        convo = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not convo:
            return False
        convo.delete()
        return True
    
        # ------------------------------------------------------------------
    # List conversations for a user
    # ------------------------------------------------------------------
    def list_user_conversations(self, user_id: str) -> List[Conversation]:
        """
        Return all conversations that include the given user as a member.
        """
        user = User.nodes.get_or_none(user_id=user_id)
        if not user:
            return []
        # Retrieve through the relationship defined in User model (member_of)
        return list(user.member_of.all())


conversation_crud = ConversationCRUD(neo4j_conn)