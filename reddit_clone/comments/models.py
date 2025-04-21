import uuid
from django.db import models
from django.utils import timezone
from users.models import User
from posts.models import Post


class Comment(models.Model):
    """
    Comment model for discussions on posts.
    Supports nested/threaded comments with materialized path.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    upvote_count = models.IntegerField(default=0)
    downvote_count = models.IntegerField(default=0)
    path = models.CharField(max_length=255)  # Materialized path for efficient tree traversal
    depth = models.IntegerField(default=0)  # Nesting level
    
    class Meta:
        db_table = 'comment'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'path']),
            models.Index(fields=['post', 'parent']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Generate path for new comments
        if is_new:
            if self.parent:
                # For replies, use parent's path + new ID
                super().save(*args, **kwargs)  # Save to get the ID first
                self.path = f"{self.parent.path}.{self.pk}"
                self.depth = self.parent.depth + 1
                kwargs['force_insert'] = False  # Since we're updating an existing record
                super().save(*args, **kwargs)  # Save again with the path
            else:
                # For top-level comments
                super().save(*args, **kwargs)  # Save to get the ID first
                self.path = str(self.pk)
                kwargs['force_insert'] = False  # Since we're updating an existing record
                super().save(*args, **kwargs)  # Save again with the path
                
            # Increment post comment count
            self.post.increment_comment_count()
        else:
            super().save(*args, **kwargs)
    
    def edit(self, content):
        """Edit the comment content."""
        self.content = content
        self.updated_at = timezone.now()
        self.is_edited = True
        self.save(update_fields=['content', 'updated_at', 'is_edited'])
    
    def soft_delete(self):
        """Soft delete the comment (hide content but keep in DB)."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])
        # Decrement post comment count
        self.post.decrement_comment_count()
    
    def update_vote_counts(self, upvotes, downvotes):
        """Update vote counts with fresh totals."""
        self.upvote_count = upvotes
        self.downvote_count = downvotes
        self.save(update_fields=['upvote_count', 'downvote_count'])
    
    def get_score(self):
        """Get the comment score (upvotes - downvotes)."""
        return self.upvote_count - self.downvote_count
    
    def get_all_replies(self):
        """Get all replies to this comment using the materialized path."""
        return Comment.objects.filter(path__startswith=f"{self.path}.", post=self.post).exclude(id=self.id)
    
    def get_reply_count(self):
        """Get the count of all replies to this comment."""
        return self.get_all_replies().count()
    
    def get_replies_by_level(self, max_depth=None):
        """Get replies grouped by level, optionally limited to max_depth."""
        replies = self.get_all_replies()
        if max_depth:
            replies = replies.filter(depth__lte=self.depth + max_depth)
        
        # Group by depth
        result = {}
        for reply in replies:
            level = reply.depth - self.depth
            if level not in result:
                result[level] = []
            result[level].append(reply)
        
        return result
