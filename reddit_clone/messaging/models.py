import uuid
from django.db import models
from django.utils import timezone
from users.models import User


class PrivateMessage(models.Model):
    """
    Private message model for direct messaging between users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_deleted_by_sender = models.BooleanField(default=False)
    is_deleted_by_recipient = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'private_message'
        verbose_name = 'Private Message'
        verbose_name_plural = 'Private Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark the message as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_deleted_by_sender(self):
        """Mark the message as deleted by the sender."""
        self.is_deleted_by_sender = True
        self.save(update_fields=['is_deleted_by_sender'])
        # If deleted by both parties, physically delete the message
        if self.is_deleted_by_recipient:
            self.delete()
    
    def mark_as_deleted_by_recipient(self):
        """Mark the message as deleted by the recipient."""
        self.is_deleted_by_recipient = True
        self.save(update_fields=['is_deleted_by_recipient'])
        # If deleted by both parties, physically delete the message
        if self.is_deleted_by_sender:
            self.delete()
    
    @classmethod
    def get_conversation(cls, user1, user2):
        """Get all messages between two users."""
        return cls.objects.filter(
            models.Q(sender=user1, recipient=user2, is_deleted_by_sender=False) |
            models.Q(sender=user2, recipient=user1, is_deleted_by_recipient=False)
        ).order_by('created_at')
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread messages for a user."""
        return cls.objects.filter(recipient=user, is_read=False, is_deleted_by_recipient=False).count()
    
    @classmethod
    def send_message(cls, sender, recipient, subject, content):
        """Create and send a new message."""
        message = cls(
            sender=sender,
            recipient=recipient,
            subject=subject,
            content=content
        )
        message.save()
        return message
