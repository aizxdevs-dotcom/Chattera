from uuid import uuid4
from app.models import Comment, User, Post

class CommentCRUD:
    def add_comment(self, user_id: str, post_id: str, text: str) -> Comment | None:
        user = User.nodes.get_or_none(user_id=user_id)
        post = Post.nodes.get_or_none(post_id=post_id)
        if not user or not post:
            return None

        comment = Comment(comment_id=str(uuid4()), text=text).save()
        user.comments.connect(comment)
        comment.post.connect(post)
        return comment

    def list_comments_for_post(self, post_id: str) -> list[Comment]:
        post = Post.nodes.get_or_none(post_id=post_id)
        if not post:
            return []
        return list(post.comments.all())

comment_crud = CommentCRUD()