from uuid import uuid4
from app.models import Post, User, File

class PostCRUD:
    def create_post(self, user_id: str, description: str = None, file_ids: list[str] = None) -> Post | None:
        user = User.nodes.get_or_none(user_id=user_id)
        if not user:
            return None

        post_id = str(uuid4())
        post_node = Post(post_id=post_id, description=description).save()

        # Connect user → authored → post
        user.authored.connect(post_node)

        # Attach files if provided
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

        # Refresh file attachments if provided
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
        if not post_node:
            return False
        post_node.delete()
        return True

    def get_post(self, post_id: str) -> Post | None:
        return Post.nodes.get_or_none(post_id=post_id)

    def list_posts_by_user(self, user_id: str) -> list[Post]:
        user = User.nodes.get_or_none(user_id=user_id)
        if not user:
            return []
        return list(user.authored.all())
    
    def list_all_posts(self) -> list[Post]:
        """Fetch all posts globally, ordered by creation date (newest first)."""
        return list(Post.nodes.order_by("-created_at"))

# instantiate
post_crud = PostCRUD()