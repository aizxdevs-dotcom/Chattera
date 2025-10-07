from uuid import uuid4
from neomodel import db
from app.models.notification import Notification
from app.models.user import User
from app.models.post import Post


class NotificationCRUD:
    @staticmethod
    def create_notification(receiver_id: str, sender_id: str, post_id: str, type_: str, message: str):
        notification_id = str(uuid4())

        notif = Notification(
            notification_id=notification_id,
            receiver_id=receiver_id,
            sender_id=sender_id,
            post_id=post_id,
            type=type_,
            message=message,
        ).save()

        # optional relationships
        try:
            sender = User.nodes.get(user_id=sender_id)
            notif.sender.connect(sender)
            post = Post.nodes.get(post_id=post_id)
            notif.post.connect(post)
        except Exception as e:
            print(f"[⚠️] Notification relationship creation failed: {e}")

        return notif

    @staticmethod
    def list_for_user(user_id: str):
        query = """
        MATCH (n:Notification {receiver_id: $user_id})
        RETURN n ORDER BY n.created_at DESC
        """
        results, _ = db.cypher_query(query, {"user_id": user_id})
        return [Notification.inflate(row[0]) for row in results]

    @staticmethod
    def mark_as_read(notification_id: str):
        notif = Notification.nodes.get_or_none(notification_id=notification_id)
        if notif:
            notif.is_read = True
            notif.save()
        return notif

    @staticmethod
    def delete_notification(notification_id: str):
        notif = Notification.nodes.get_or_none(notification_id=notification_id)
        if notif:
            notif.delete()
            return True
        return False


notification_crud = NotificationCRUD()