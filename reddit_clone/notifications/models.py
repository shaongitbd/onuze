import uuid
from django.db import models
from django.utils import timezone
from users.models import User


class Notification(models.Model):
    """
    Notification model for tracking user notifications.
    Uses polymorphic relationship for content_type and content_id.
    """
    # Notification types
    COMMENT_REPLY = 'comment_reply'
    POST_REPLY = 'post_reply'
    MENTION = 'mention'
    MOD_ACTION = 'mod_action'
    VOTE_MILESTONE = 'vote_milestone'
    WELCOME = 'welcome'
    NOTIFICATION_TYPES = [
        (COMMENT_REPLY, 'Comment Reply'),
        (POST_REPLY, 'Post Reply'),
        (MENTION, 'Mention'),
        (MOD_ACTION, 'Moderator Action'),
        (VOTE_MILESTONE, 'Vote Milestone'),
        (WELCOME, 'Welcome'),
    ]
    
    # Content types
    POST = 'post'
    COMMENT = 'comment'
    MESSAGE = 'message'
    COMMUNITY = 'community'
    USER = 'user'
    CONTENT_TYPES = [
        (POST, 'Post'),
        (COMMENT, 'Comment'),
        (MESSAGE, 'Message'),
        (COMMUNITY, 'Community'),
        (USER, 'User'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES)
    content_id = models.UUIDField()
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    link_url = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.notification_type}"
    
    def mark_as_read(self):
        """Mark the notification as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])
    
    def mark_as_unread(self):
        """Mark the notification as unread."""
        self.is_read = False
        self.save(update_fields=['is_read'])
    
    @classmethod
    def send_notification(cls, user, notification_type, content_type, content_id, message, sender=None, link_url=None):
        """Create and send a notification to a user."""
        notification = cls(
            user=user,
            sender=sender,
            notification_type=notification_type,
            content_type=content_type,
            content_id=content_id,
            message=message,
            link_url=link_url
        )
        notification.save()
        return notification
    
    @classmethod
    def send_comment_reply_notification(cls, comment):
        """Send a notification for a reply to a comment."""
        # Only send if the parent comment author is not the same as the reply author
        if comment.parent and comment.parent.user != comment.user:
            return cls.send_notification(
                user=comment.parent.user,
                notification_type=cls.COMMENT_REPLY,
                content_type=cls.COMMENT,
                content_id=comment.id,
                message=f"{comment.user.username} replied to your comment",
                sender=comment.user,
                link_url=f"/post/{comment.post.id}/comment/{comment.id}"
            )
        return None
    
    @classmethod
    def send_post_reply_notification(cls, comment):
        """Send a notification for a reply to a post."""
        # Only send if the post author is not the same as the comment author
        if comment.post.user != comment.user:
            return cls.send_notification(
                user=comment.post.user,
                notification_type=cls.POST_REPLY,
                content_type=cls.COMMENT,
                content_id=comment.id,
                message=f"{comment.user.username} commented on your post",
                sender=comment.user,
                link_url=f"/post/{comment.post.id}/comment/{comment.id}"
            )
        return None
    
    @classmethod
    def send_vote_milestone_notification(cls, content_type, content_obj, milestone):
        """Send a notification for a vote milestone (e.g., 10, 50, 100 upvotes)."""
        if content_type == cls.POST:
            return cls.send_notification(
                user=content_obj.user,
                notification_type=cls.VOTE_MILESTONE,
                content_type=cls.POST,
                content_id=content_obj.id,
                message=f"Your post reached {milestone} upvotes!",
                link_url=f"/post/{content_obj.id}"
            )
        elif content_type == cls.COMMENT:
            return cls.send_notification(
                user=content_obj.user,
                notification_type=cls.VOTE_MILESTONE,
                content_type=cls.COMMENT,
                content_id=content_obj.id,
                message=f"Your comment reached {milestone} upvotes!",
                link_url=f"/post/{content_obj.post.id}/comment/{content_obj.id}"
            )
        return None
    
    @classmethod
    def send_mod_action_notification(cls, user, community, action, admin_user, link_url=None):
        """Send a notification for a moderator action."""
        return cls.send_notification(
            user=user,
            notification_type=cls.MOD_ACTION,
            content_type=cls.COMMUNITY,
            content_id=community.id,
            message=f"Moderator action: {action} in {community.name}",
            sender=admin_user,
            link_url=link_url
        )
    
    @classmethod
    def send_welcome_notification(cls, user):
        """Send a welcome notification to a new user."""
        return cls.send_notification(
            user=user,
            notification_type=cls.WELCOME,
            content_type=cls.USER,
            content_id=user.id,
            message=f"Welcome to Reddit Clone, {user.username}! We're glad you're here.",
            link_url="/help/getting-started"
        )
