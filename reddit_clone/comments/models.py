import uuid
from django.db import models
from django.utils import timezone
from users.models import User
from posts.models import Post
from django.db.models import F
from django.db import transaction
import logging


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
    reply_count = models.IntegerField(default=0)  # Count of direct replies to this comment
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
        logger = logging.getLogger('django')
        
        # Check if this is a truly new instance by looking at self.id/self.pk/path
        force_new = kwargs.pop('force_new', False)
        if force_new or not self.pk or not self.id or self.pk == '' or self.id == '' or self.path == '':
            logger.info(f"Forcing is_new=True for comment - id: {self.id}, pk: {self.pk}, path: {self.path}")
            is_new = True
        else:
            is_new = self.pk is None
        
        logger.info(f"Saving comment: is_new={is_new}, id={self.id}, pk={self.pk}, path={self.path}")
        
        # Generate path for new comments
        if is_new:
            try:
                with transaction.atomic():
                    # Determine path and depth based on parent
                    if self.parent:
                        logger.info(f"Creating reply to existing comment {self.parent.id}")
                        parent_path = self.parent.path
                        self.depth = self.parent.depth + 1
                        last_sibling = Comment.objects.filter(parent=self.parent).order_by('-path').first()
                    else:
                        logger.info(f"Creating top-level comment for post {self.post.id}")
                        parent_path = ''
                        self.depth = 1
                        last_sibling = Comment.objects.filter(post=self.post, parent__isnull=True).order_by('-path').first()

                    # Generate the next path segment
                    if last_sibling:
                        last_segment_str = last_sibling.path.split('.')[-1]
                        try:
                            last_segment = int(last_segment_str)
                            next_segment = last_segment + 1
                        except ValueError:
                            logger.error(f"Could not parse last path segment '{last_segment_str}' for sibling {last_sibling.id}. Using 1.")
                            next_segment = 1 # Fallback if parsing fails
                    else:
                        next_segment = 1

                    # Format the path segment (e.g., 4 digits with leading zeros)
                    path_segment = f"{next_segment:04d}"

                    # Construct the full path
                    if parent_path:
                        self.path = f"{parent_path}.{path_segment}"
                    else:
                        self.path = path_segment
                        
                    logger.info(f"Generated path: {self.path}, Depth: {self.depth}")

                    # Save the comment *first* to get the ID (if new) and update path/depth
                    # Use super().save() to avoid recursion
                    super(Comment, self).save(force_insert=True, using=kwargs.get('using')) 
                    logger.info(f"Comment saved with ID: {self.id} and Path: {self.path}")
                
                    # Increment post comment count
                    logger.info(f"Calling increment_comment_count for post {self.post.id}")
                    self.post.increment_comment_count()
                    # Refresh post to log updated count
                    self.post.refresh_from_db(fields=['comment_count'])
                    logger.info(f"After increment, post comment_count={self.post.comment_count}")
                    
                    # Increment parent reply count if applicable
                    if self.parent:
                        logger.info(f"Incrementing reply count for parent comment {self.parent.id}")
                        Comment.objects.filter(pk=self.parent.pk).update(reply_count=F('reply_count') + 1)
                        logger.info(f"Parent comment {self.parent.id} reply count updated.")
                        
            except Exception as e:
                logger.error(f"Error in comment save transaction: {str(e)}", exc_info=True)
                raise
        else:
            # Handle updates to existing comments
            logger.info(f"Updating existing comment {self.id}")
            # Automatically update 'updated_at' timestamp
            self.updated_at = timezone.now()
            kwargs['update_fields'] = list(kwargs.get('update_fields', [])) + ['updated_at', 'is_edited']
            # Ensure 'content' is included if it's being changed
            if 'content' in kwargs.get('update_fields', []):
                 self.is_edited = True
            else:
                # Avoid setting is_edited if only votes changed, etc.
                 if 'is_edited' in kwargs['update_fields']:
                     kwargs['update_fields'].remove('is_edited')
            
            super(Comment, self).save(*args, **kwargs)
    
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
        Comment.objects.filter(id=self.id).update(
            upvote_count=upvotes,
            downvote_count=downvotes
        )
        # Refresh from DB to keep the instance in sync
        self.refresh_from_db(fields=['upvote_count', 'downvote_count'])
    
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
