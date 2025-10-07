from uuid import uuid4
from app.models import Reaction, User, Post
from app.crud.notification import notification_crud


class ReactionCRUD:
    def add_or_update_reaction(
        self,
        user_id: str,
        post_id: str,
        type: str
    ) -> Reaction | None:
        """
        Add or update a reaction for a post.
        Generates a notification for the post author
        if the reacting user is not the author.
        """
        user = User.nodes.get_or_none(user_id=user_id)
        post = Post.nodes.get_or_none(post_id=post_id)
        if not user or not post:
            return None

        # find existing reaction by this user for this post
        existing_reaction = None
        for r in post.reactions:
            u = r.user.single()
            if u and u.user_id == user_id:
                existing_reaction = r
                break

        # update existing reaction if found
        if existing_reaction:
            if existing_reaction.type != type:
                existing_reaction.type = type
                existing_reaction.save()
            return existing_reaction

        reaction = Reaction(reaction_id=str(uuid4()), type=type).save()
        user.reactions.connect(reaction)
        reaction.post.connect(post)

        # ---- Notification logic ----
        try:
            author = post.author.single()
            # only notify if liking/commenting on another user's post
            if author and author.user_id != user.user_id:
                message = f"{user.username} reacted '{type}' to your post"
                notification_crud.create_notification(
                    receiver_id=author.user_id,
                    sender_id=user.user_id,
                    post_id=post.post_id,
                    type_="reaction",
                    message=message,
                )
        except Exception as e:
            print(f"[⚠️] Failed to create reaction notification: {e}")

        return reaction

    def list_reactions_for_post(self, post_id: str) -> list[Reaction]:
        post = Post.nodes.get_or_none(post_id=post_id)
        if not post:
            return []
        return list(post.reactions.all())


reaction_crud = ReactionCRUD()