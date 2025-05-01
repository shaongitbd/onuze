import uuid
from django.db import models
from django.utils import timezone
from users.models import User


class SearchHistory(models.Model):
    """
    Model to track user search history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='searches', null=True, blank=True)
    query = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    result_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'search_history'
        verbose_name = 'Search History'
        verbose_name_plural = 'Search Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['query']),
        ]
    
    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"Search by {username}: {self.query}" 