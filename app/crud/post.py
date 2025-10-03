from uuid import uuid4
from app.models import Post, User, File, Comment

class PostCRUD:
    def create_post(self, user_id: str, description: str = None, file_ids: list[str] = None) -> Post | None:
        user = User.nodes.get_or_none(user_id=user_id)
        if not user:
            return None

        post_id = str(uuid4())
        post_node = Post(post_id=post_id, description=description).save()
        user.authored.connect(post_node)

        if file_ids:
            for fid in file_ids:
                file_node = File.nodes.get_or_none(file_id=fid)
                if file_node:
                    post_node.attachments.connect(file_node)

        return post_node

    def update_post(self, post_id: str, description: str | None = None, file_ids: list[str] | None = None) -> Post | None:
        post_node = Post.nodes.get_or_none(post_id=post_id)
        if not post_node:
            return None

        if description is not None:
            post_node.description = description

        if file_ids is not None:
            post_node.attachments.disconnect_all()
            for fid in file_ids:
                file_node = File.nodes.get_or_none(file_id=fid)
                if file_node:
                    post_node.attachments.connect(file_node)

        post_node.save()
        return post_node

    def delete_post(self, post_id: str) -> bool:
        post_node = Post.nodes.get_or_none(post_id=post_id)
        if not post_node: return False
        post_node.delete()
        return True

    def get_post(self, post_id: str) -> Post | None:
        return Post.nodes.get_or_none(post_id=post_id)

    def list_posts_by_user(self, user_id: str) -> list[Post]:
        user = User.nodes.get_or_none(user_id=user_id)
        if not user: return []
        return list(user.authored.order_by("-created_at"))

    def list_all_posts(self) -> list[Post]:
        """Global feed: all posts by all users, ordered newest first"""
        return list(Post.nodes.order_by("-created_at"))
    
    def get_reaction_counts(self, post) -> dict[str, int]:
        counts = {"like": 0, "haha": 0, "sad": 0, "angry": 0, "care": 0}
        for r in post.reactions:
            if r.type in counts:
                counts[r.type] += 1
        return counts
    
    def get_reaction_counts(self, post) -> dict[str, int]:
        counts = {"like": 0, "haha": 0, "sad": 0, "angry": 0, "care": 0}
        for r in post.reactions:
            if r.type in counts:
                counts[r.type] += 1
        return counts

    def get_user_reaction(self, post, user_id: str) -> str | None:
        """Return the current user’s reaction type on this post, or None."""
        for r in post.reactions:
            u = r.user.single()
            if u and u.user_id == user_id:
                return r.type
        return None
    
post_crud = PostCRUD()