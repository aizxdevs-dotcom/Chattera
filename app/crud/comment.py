from uuid import uuid4
from app.models import Comment, User, Post, File

class CommentCRUD:
    def add_comment(self, user_id: str, post_id: str, description: str = None, file_ids: list[str] = None) -> Comment | None:
        user = User.nodes.get_or_none(user_id=user_id)
        post = Post.nodes.get_or_none(post_id=post_id)
        if not user or not post:
            return None

        comment = Comment(comment_id=str(uuid4()), description=description).save()

        # connect user + post
        user.comments.connect(comment)
        comment.post.connect(post)

        # attach any files
        if file_ids:
            for fid in file_ids:
                file_node = File.nodes.get_or_none(file_id=fid)
                if file_node:
                    comment.attachments.connect(file_node)

        return comment

    def list_comments_for_post(self, post_id: str) -> list[Comment]:
        post = Post.nodes.get_or_none(post_id=post_id)
        if not post:
            return []
        return list(post.comments.order_by("created_at"))
    
    def get_reaction_counts(self, comment) -> dict[str, int]:
        counts = {"like": 0, "haha": 0, "sad": 0, "angry": 0, "care": 0}
        for r in comment.reactions:
            if r.type in counts:
                counts[r.type] += 1
        return counts

    def get_user_reaction(self, comment, user_id: str) -> str | None:
        for r in comment.reactions:
            u = r.user.single()
            if u and u.user_id == user_id:
                return r.type
        return None

comment_crud = CommentCRUD()