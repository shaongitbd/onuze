import uuid
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
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
    path = models.SlugField(max_length=350, unique=True, blank=True, null=True)
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
            models.Index(fields=['path']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Generate a slug if one doesn't exist
        if not self.path:
            # Base the slug on the title
            base_slug = slugify(self.title)
            if len(base_slug) > 80:  # Keep slug reasonable length
                base_slug = base_slug[:80]
            
            # Check if the slug already exists
            slug = base_slug
            counter = 1
            while Post.objects.filter(path=slug).exists():
                # If slug exists, append a counter
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.path = slug
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return the URL for this post."""
        return f"/posts/{self.path}/"
    
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


class Vote(models.Model):
    """
    Vote model for post voting.
    """
    VOTE_TYPES = (
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_votes')
    vote_type = models.CharField(max_length=10, choices=VOTE_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'post_vote'
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'
        unique_together = ['post', 'user']  # One vote per user per post
    
    def __str__(self):
        return f"{self.user.username} {self.vote_type} on {self.post.title}"


class PostImage(models.Model):
    """
    Image linked to posts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image_url = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'post_image'
        verbose_name = 'Post Image'
        verbose_name_plural = 'Post Images'
        ordering = ['post', 'order']
    
    def __str__(self):
        return f"Image for {self.post.title} ({self.order})"


class PostReport(models.Model):
    """
    Report model for posts.
    """
    REPORT_REASONS = (
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('violence', 'Violence'),
        ('misinformation', 'Misinformation'),
        ('hate', 'Hate Speech'),
        ('self_harm', 'Self Harm'),
        ('nsfw', 'NSFW Content Not Marked'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reports')
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_post_reports')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'post_report'
        verbose_name = 'Post Report'
        verbose_name_plural = 'Post Reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report on {self.post.title} by {self.user.username}"
    
    def resolve(self, user):
        """Mark the report as resolved."""
        self.resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save(update_fields=['resolved', 'resolved_by', 'resolved_at'])


class PostSave(models.Model):
    """
    Saved posts model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saves')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'post_save'
        verbose_name = 'Saved Post'
        verbose_name_plural = 'Saved Posts'
        unique_together = ['post', 'user']  # Each user can save a post only once
    
    def __str__(self):
        return f"{self.user.username} saved {self.post.title}"
