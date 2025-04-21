import uuid
from django.db import models
from django.utils import timezone
from django.db.models import F
from users.models import User
from posts.models import Post
from comments.models import Comment


class Vote(models.Model):
    """
    Vote model for tracking upvotes and downvotes on posts and comments.
    Uses polymorphic relationship for content_type and content_id.
    """
    # Vote types
    DOWNVOTE = -1
    UPVOTE = 1
    VOTE_TYPES = [
        (DOWNVOTE, 'Downvote'),
        (UPVOTE, 'Upvote'),
    ]
    
    # Content types
    POST = 'post'
    COMMENT = 'comment'
    CONTENT_TYPES = [
        (POST, 'Post'),
        (COMMENT, 'Comment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES)
    content_id = models.UUIDField()
    vote_type = models.SmallIntegerField(choices=VOTE_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'vote'
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'
        # Ensure one vote per user per content
        unique_together = ('user', 'content_type', 'content_id')
        indexes = [
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['user', 'content_type']),
        ]
    
    def __str__(self):
        vote_label = 'upvote' if self.vote_type == self.UPVOTE else 'downvote'
        return f"{self.user.username}'s {vote_label} on {self.content_type} {self.content_id}"
    
    def save(self, *args, **kwargs):
        # Track if this is a new vote or an update
        is_new = self.pk is None
        if not is_new:
            old_instance = Vote.objects.get(pk=self.pk)
            old_vote_type = old_instance.vote_type
        else:
            old_vote_type = None
        
        # Save the vote
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
        
        # Update the vote counts on the content
        self._update_content_vote_counts(is_new, old_vote_type)
        
        # Update user karma
        if self.content_type == self.POST and hasattr(self, 'post'):
            # Karma impact is higher for posts
            self._update_user_karma(is_new, old_vote_type, multiplier=2)
        else:
            self._update_user_karma(is_new, old_vote_type)
    
    def delete(self, *args, **kwargs):
        # Store vote info before deletion
        vote_type = self.vote_type
        
        super().delete(*args, **kwargs)
        
        # Update content vote counts after deletion
        self._update_content_vote_counts(is_new=False, old_vote_type=vote_type, is_deletion=True)
        
        # Update user karma
        self._update_user_karma(is_new=False, old_vote_type=vote_type, is_deletion=True)
    
    def _update_content_vote_counts(self, is_new, old_vote_type, is_deletion=False):
        """Update vote counts on the content (post or comment)."""
        if self.content_type == self.POST:
            try:
                post = Post.objects.get(id=self.content_id)
                
                # Calculate updated vote counts
                upvotes = post.upvote_count
                downvotes = post.downvote_count
                
                if is_deletion:
                    # Removing a vote
                    if old_vote_type == self.UPVOTE:
                        upvotes -= 1
                    elif old_vote_type == self.DOWNVOTE:
                        downvotes -= 1
                elif is_new:
                    # Adding a new vote
                    if self.vote_type == self.UPVOTE:
                        upvotes += 1
                    elif self.vote_type == self.DOWNVOTE:
                        downvotes += 1
                else:
                    # Changing vote type
                    if old_vote_type == self.UPVOTE and self.vote_type == self.DOWNVOTE:
                        upvotes -= 1
                        downvotes += 1
                    elif old_vote_type == self.DOWNVOTE and self.vote_type == self.UPVOTE:
                        downvotes -= 1
                        upvotes += 1
                
                # Update the post
                post.update_vote_counts(upvotes, downvotes)
                
            except Post.DoesNotExist:
                pass  # Post may have been deleted
                
        elif self.content_type == self.COMMENT:
            try:
                comment = Comment.objects.get(id=self.content_id)
                
                # Calculate updated vote counts
                upvotes = comment.upvote_count
                downvotes = comment.downvote_count
                
                if is_deletion:
                    # Removing a vote
                    if old_vote_type == self.UPVOTE:
                        upvotes -= 1
                    elif old_vote_type == self.DOWNVOTE:
                        downvotes -= 1
                elif is_new:
                    # Adding a new vote
                    if self.vote_type == self.UPVOTE:
                        upvotes += 1
                    elif self.vote_type == self.DOWNVOTE:
                        downvotes += 1
                else:
                    # Changing vote type
                    if old_vote_type == self.UPVOTE and self.vote_type == self.DOWNVOTE:
                        upvotes -= 1
                        downvotes += 1
                    elif old_vote_type == self.DOWNVOTE and self.vote_type == self.UPVOTE:
                        downvotes -= 1
                        upvotes += 1
                
                # Update the comment
                comment.update_vote_counts(upvotes, downvotes)
                
            except Comment.DoesNotExist:
                pass  # Comment may have been deleted
    
    def _update_user_karma(self, is_new, old_vote_type, multiplier=1, is_deletion=False):
        """Update the user's karma based on the vote."""
        try:
            # Get the author of the content
            if self.content_type == self.POST:
                content_author = Post.objects.get(id=self.content_id).user
            elif self.content_type == self.COMMENT:
                content_author = Comment.objects.get(id=self.content_id).user
            else:
                return  # Unknown content type
            
            # Skip if voting on own content
            if content_author == self.user:
                return
            
            # Calculate karma change
            karma_change = 0
            
            if is_deletion:
                # Removing a vote
                if old_vote_type == self.UPVOTE:
                    karma_change = -1 * multiplier
                elif old_vote_type == self.DOWNVOTE:
                    karma_change = 1 * multiplier
            elif is_new:
                # Adding a new vote
                if self.vote_type == self.UPVOTE:
                    karma_change = 1 * multiplier
                elif self.vote_type == self.DOWNVOTE:
                    karma_change = -1 * multiplier
            else:
                # Changing vote type
                if old_vote_type == self.UPVOTE and self.vote_type == self.DOWNVOTE:
                    karma_change = -2 * multiplier
                elif old_vote_type == self.DOWNVOTE and self.vote_type == self.UPVOTE:
                    karma_change = 2 * multiplier
            
            # Update the user's karma
            if karma_change > 0:
                content_author.increment_karma(amount=karma_change)
            elif karma_change < 0:
                content_author.decrement_karma(amount=abs(karma_change))
                
        except (Post.DoesNotExist, Comment.DoesNotExist):
            pass  # Content may have been deleted
    
    @property
    def post(self):
        """Get the related post if content_type is POST."""
        if self.content_type == self.POST:
            try:
                return Post.objects.get(id=self.content_id)
            except Post.DoesNotExist:
                return None
        return None
    
    @property
    def comment(self):
        """Get the related comment if content_type is COMMENT."""
        if self.content_type == self.COMMENT:
            try:
                return Comment.objects.get(id=self.content_id)
            except Comment.DoesNotExist:
                return None
        return None
    
    @classmethod
    def create_or_update(cls, user, content_type, content_id, vote_type):
        """Create a new vote or update an existing one."""
        try:
            vote = cls.objects.get(
                user=user,
                content_type=content_type,
                content_id=content_id
            )
            
            # If vote type is the same, remove the vote (toggle)
            if vote.vote_type == vote_type:
                vote.delete()
                return None
            else:
                vote.vote_type = vote_type
                vote.updated_at = timezone.now()
                vote.save()
                return vote
                
        except cls.DoesNotExist:
            # Create a new vote
            vote = cls(
                user=user,
                content_type=content_type,
                content_id=content_id,
                vote_type=vote_type
            )
            vote.save()
            return vote
