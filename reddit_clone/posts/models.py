import uuid
from django.db import models
from django.utils import timezone
from users.models import User
from communities.models import Community, Flair


class Post(models.Model):
    """
    Post model for submissions in communities.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=300)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='locked_posts')
    locked_reason = models.TextField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    flair = models.ForeignKey(Flair, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    upvote_count = models.IntegerField(default=0)
    downvote_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    is_nsfw = models.BooleanField(default=False)
    is_spoiler = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'post'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['community', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def edit(self, content):
        """Edit the post content."""
        self.content = content
        self.updated_at = timezone.now()
        self.is_edited = True
        self.save(update_fields=['content', 'updated_at', 'is_edited'])
    
    def soft_delete(self):
        """Soft delete the post (hide it but keep in DB)."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])
    
    def lock(self, locked_by, reason=None):
        """Lock the post to prevent new comments."""
        self.is_locked = True
        self.locked_by = locked_by
        self.locked_reason = reason
        self.save(update_fields=['is_locked', 'locked_by', 'locked_reason'])
    
    def unlock(self):
        """Unlock the post to allow new comments."""
        self.is_locked = False
        self.locked_reason = None
        self.save(update_fields=['is_locked', 'locked_reason'])
    
    def pin(self):
        """Pin the post to the top of the community."""
        self.is_pinned = True
        self.save(update_fields=['is_pinned'])
    
    def unpin(self):
        """Unpin the post from the top of the community."""
        self.is_pinned = False
        self.save(update_fields=['is_pinned'])
    
    def increment_view_count(self):
        """Increment the view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_comment_count(self):
        """Increment the comment count."""
        self.comment_count += 1
        self.save(update_fields=['comment_count'])
    
    def decrement_comment_count(self):
        """Decrement the comment count."""
        if self.comment_count > 0:
            self.comment_count -= 1
            self.save(update_fields=['comment_count'])
    
    def update_vote_counts(self, upvotes, downvotes):
        """Update vote counts with fresh totals."""
        self.upvote_count = upvotes
        self.downvote_count = downvotes
        self.save(update_fields=['upvote_count', 'downvote_count'])
    
    def get_score(self):
        """Get the post score (upvotes - downvotes)."""
        return self.upvote_count - self.downvote_count


class PostMedia(models.Model):
    """
    Media linked to posts (images, videos, etc.).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=50)  # image, video, gif, etc.
    media_url = models.CharField(max_length=255)
    thumbnail_url = models.CharField(max_length=255, null=True, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'post_media'
        verbose_name = 'Post Media'
        verbose_name_plural = 'Post Media'
        ordering = ['post', 'order']
    
    def __str__(self):
        return f"{self.post.title} - {self.media_type} ({self.order})"
