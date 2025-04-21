import uuid
from django.db import models
from django.utils import timezone
from users.models import User
from communities.models import Community


class Report(models.Model):
    """
    Report model for users to report problematic content.
    Uses polymorphic relationship for content_type and content_id.
    """
    # Report statuses
    PENDING = 'pending'
    RESOLVED = 'resolved'
    REJECTED = 'rejected'
    STATUSES = [
        (PENDING, 'Pending'),
        (RESOLVED, 'Resolved'),
        (REJECTED, 'Rejected'),
    ]
    
    # Content types
    POST = 'post'
    COMMENT = 'comment'
    USER = 'user'
    CONTENT_TYPES = [
        (POST, 'Post'),
        (COMMENT, 'Comment'),
        (USER, 'User'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES)
    content_id = models.UUIDField()
    reason = models.CharField(max_length=100)
    details = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, choices=STATUSES, default=PENDING)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='reports')
    
    class Meta:
        db_table = 'report'
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['community', 'status']),
            models.Index(fields=['content_type', 'content_id']),
        ]
    
    def __str__(self):
        return f"Report by {self.reporter.username} ({self.status})"
    
    def resolve(self, resolved_by, notes=None):
        """Mark the report as resolved."""
        self.status = self.RESOLVED
        self.resolved_by = resolved_by
        self.resolved_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save(update_fields=['status', 'resolved_by', 'resolved_at', 'resolution_notes'])
    
    def reject(self, resolved_by, notes=None):
        """Mark the report as rejected."""
        self.status = self.REJECTED
        self.resolved_by = resolved_by
        self.resolved_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        self.save(update_fields=['status', 'resolved_by', 'resolved_at', 'resolution_notes'])


class BanAppeal(models.Model):
    """
    BanAppeal model for users to appeal community or site-wide bans.
    """
    # Appeal statuses
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUSES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    
    # Appeal types
    COMMUNITY_BAN = 'community_ban'
    SITE_BAN = 'site_ban'
    APPEAL_TYPES = [
        (COMMUNITY_BAN, 'Community Ban'),
        (SITE_BAN, 'Site Ban'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ban_appeals')
    appeal_type = models.CharField(max_length=50, choices=APPEAL_TYPES)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, null=True, blank=True, related_name='ban_appeals')
    reason = models.TextField()
    evidence = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUSES, default=PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_appeals')
    reviewer_notes = models.TextField(null=True, blank=True)
    response_to_user = models.TextField(null=True, blank=True)
    original_ban_reason = models.TextField(null=True, blank=True)
    original_banned_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ban_appeal'
        verbose_name = 'Ban Appeal'
        verbose_name_plural = 'Ban Appeals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['appeal_type', 'status']),
            models.Index(fields=['community', 'status']),
        ]
    
    def __str__(self):
        if self.appeal_type == self.COMMUNITY_BAN and self.community:
            return f"{self.user.username}'s appeal for {self.community.name} ban"
        return f"{self.user.username}'s appeal for site ban"
    
    def approve(self, reviewed_by, notes=None, response=None):
        """Approve the ban appeal."""
        self.status = self.APPROVED
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        if notes:
            self.reviewer_notes = notes
        if response:
            self.response_to_user = response
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_notes', 'response_to_user'])
        
        # Unban the user
        if self.appeal_type == self.COMMUNITY_BAN and self.community:
            try:
                from communities.models import CommunityMember
                member = CommunityMember.objects.get(user=self.user, community=self.community)
                member.unban()
            except Exception:
                pass
        elif self.appeal_type == self.SITE_BAN:
            self.user.remove_site_ban()
    
    def reject(self, reviewed_by, notes=None, response=None):
        """Reject the ban appeal."""
        self.status = self.REJECTED
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        if notes:
            self.reviewer_notes = notes
        if response:
            self.response_to_user = response
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_notes', 'response_to_user'])