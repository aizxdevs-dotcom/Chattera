from uuid import uuid4
from app.models import Reaction, User, Post

class ReactionCRUD:
    def add_or_update_reaction(self, user_id: str, post_id: str, type: str) -> Reaction | None:
        user = User.nodes.get_or_none(user_id=user_id)
        post = Post.nodes.get_or_none(post_id=post_id)
        if not user or not post:
            return None

        # Ensure only one reaction per user per post
        existing = (
            Reaction.nodes.match(user=user, post=post).first()
            if hasattr(Reaction.nodes, "match") else None
        )

        if existing:
            existing.type = type
            existing.save()
            return existing

        reaction = Reaction(reaction_id=str(uuid4()), type=type).save()
        user.reactions.connect(reaction)
        reaction.post.connect(post)
        return reaction
    
    def list_reactions_for_post(self, post_id: str) -> list[Reaction]:
        post = Post.nodes.get_or_none(post_id=post_id)
        if not post:
            return []
        return list(post.reactions.all())

reaction_crud = ReactionCRUD()