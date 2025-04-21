import uuid
from django.db import models
from django.utils import timezone
from users.models import User


class Community(models.Model):
    """
    Community (Subreddit) model.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_communities')
    sidebar_content = models.TextField(null=True, blank=True)
    banner_image = models.CharField(max_length=255, null=True, blank=True)
    icon_image = models.CharField(max_length=255, null=True, blank=True)
    is_private = models.BooleanField(default=False)
    member_count = models.IntegerField(default=0)
    is_nsfw = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'community'
        verbose_name = 'Community'
        verbose_name_plural = 'Communities'
        ordering = ['-member_count']
    
    def __str__(self):
        return self.name
    
    def increment_member_count(self):
        """Increment the member count."""
        self.member_count += 1
        self.save(update_fields=['member_count'])
    
    def decrement_member_count(self):
        """Decrement the member count."""
        if self.member_count > 0:
            self.member_count -= 1
            self.save(update_fields=['member_count'])


class CommunityMember(models.Model):
    """
    Many-to-many relationship between communities and users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='communities')
    joined_at = models.DateTimeField(default=timezone.now)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(null=True, blank=True)
    banned_until = models.DateTimeField(null=True, blank=True)
    banned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='banned_community_members')
    
    class Meta:
        db_table = 'community_member'
        verbose_name = 'Community Member'
        verbose_name_plural = 'Community Members'
        unique_together = ('community', 'user')
    
    def __str__(self):
        return f"{self.user.username} in {self.community.name}"
    
    def ban(self, reason, banned_by, duration_days=None):
        """Ban the user from the community."""
        self.is_banned = True
        self.ban_reason = reason
        self.banned_by = banned_by
        
        if duration_days:
            self.banned_until = timezone.now() + timezone.timedelta(days=duration_days)
        
        self.save(update_fields=['is_banned', 'ban_reason', 'banned_by', 'banned_until'])
    
    def unban(self):
        """Unban the user from the community."""
        self.is_banned = False
        self.banned_until = None
        self.save(update_fields=['is_banned', 'banned_until'])
    
    def is_banned_now(self):
        """Check if the user is currently banned."""
        if not self.is_banned:
            return False
        
        # If there's an end date and it's in the past, unban automatically
        if self.banned_until and timezone.now() > self.banned_until:
            self.unban()
            return False
        
        return True


class CommunityModerator(models.Model):
    """
    Many-to-many relationship between communities and moderators (users).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='moderators')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moderated_communities')
    appointed_at = models.DateTimeField(default=timezone.now)
    appointed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='appointed_moderators')
    permissions = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'community_moderator'
        verbose_name = 'Community Moderator'
        verbose_name_plural = 'Community Moderators'
        unique_together = ('community', 'user')
    
    def __str__(self):
        return f"{self.user.username} moderates {self.community.name}"
    
    def has_permission(self, permission):
        """Check if the moderator has a specific permission."""
        return self.permissions.get(permission, False)
    
    def set_permission(self, permission, value=True):
        """Set a permission value for the moderator."""
        self.permissions[permission] = value
        self.save(update_fields=['permissions'])


class CommunityRule(models.Model):
    """
    Rules for a community.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='rules')
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rules')
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'community_rule'
        verbose_name = 'Community Rule'
        verbose_name_plural = 'Community Rules'
        ordering = ['community', 'order']
    
    def __str__(self):
        return f"{self.community.name} - {self.title}"


class Flair(models.Model):
    """
    Flairs that can be applied to posts in a community.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='flairs')
    name = models.CharField(max_length=100)
    background_color = models.CharField(max_length=7, default="#FFFFFF")  # Hex color
    text_color = models.CharField(max_length=7, default="#000000")  # Hex color
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_flairs')
    is_mod_only = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'flair'
        verbose_name = 'Flair'
        verbose_name_plural = 'Flairs'
        ordering = ['community', 'name']
    
    def __str__(self):
        return f"{self.community.name} - {self.name}"
