from app.config import neo4j_conn
from app.models import Conversation, User


class ConversationCRUD:
    def __init__(self, connection):
        self.connection = connection

    def create_conversation(self, conversation_id: str, is_group: bool, member_ids: list[str]):
        conversation = Conversation(
            conversation_id=conversation_id,
            is_group=is_group
        ).save()

        for member_id in member_ids:
            user = User.nodes.get(user_id=member_id)
            user.member_of.connect(conversation)

        return conversation
    def add_member(self, conversation_id: str, user_id: str) -> Conversation | None:
        """Add a member (User) to an existing conversation."""
        conversation = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not conversation:
            return None

        user = User.nodes.get_or_none(user_id=user_id)
        if not user:
            return None

        user.member_of.connect(conversation)
        return conversation
    def remove_member(self, conversation_id: str, user_id: str) -> Conversation | None:
        """Remove a member (User) from an existing conversation."""
        conversation = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not conversation:
            return None

        user = User.nodes.get_or_none(user_id=user_id)
        if not user:
            return None

        # disconnect relationship if it exists
        user.member_of.disconnect(conversation)
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        return Conversation.nodes.get_or_none(conversation_id=conversation_id)

    def update_conversation(self, conversation_id: str, is_group: bool = None) -> Conversation | None:
        """Update a conversation’s properties (currently only is_group)."""
        conversation = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not conversation:
            return None
        if is_group is not None:
            conversation.is_group = is_group
        conversation.save()
        return conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation node and all its relationships."""
        conversation = Conversation.nodes.get_or_none(conversation_id=conversation_id)
        if not conversation:
            return False
        conversation.delete()
        return True



conversation_crud = ConversationCRUD(neo4j_conn)