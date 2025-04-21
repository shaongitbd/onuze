import uuid
from django.db import models
from django.utils import timezone
from users.models import User


class RefreshToken(models.Model):
    """
    Model to store JWT refresh tokens.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    issued_by_ip = models.CharField(max_length=45, null=True, blank=True)
    
    class Meta:
        db_table = 'refresh_token'
        verbose_name = 'Refresh Token'
        verbose_name_plural = 'Refresh Tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        status = "revoked" if self.revoked else "active"
        return f"{self.user.username}'s token ({status})"
    
    def is_valid(self):
        """Check if token is valid (not expired, not revoked)."""
        return not self.revoked and timezone.now() < self.expires_at
    
    def revoke(self):
        """Revoke the token."""
        self.revoked = True
        self.revoked_at = timezone.now()
        self.save(update_fields=['revoked', 'revoked_at'])
    
    @classmethod
    def revoke_all_for_user(cls, user):
        """Revoke all refresh tokens for a user."""
        now = timezone.now()
        return cls.objects.filter(user=user, revoked=False).update(
            revoked=True,
            revoked_at=now
        )


class EmailVerification(models.Model):
    """
    Model to store email verification tokens.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verification'
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        status = "verified" if self.is_verified else "pending"
        return f"{self.user.email} verification ({status})"
    
    def is_valid(self):
        """Check if token is valid (not expired, not verified)."""
        return not self.is_verified and timezone.now() < self.expires_at
    
    def verify(self):
        """Mark token as verified and user as verified."""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_at'])
        
        # Update user as verified
        self.user.is_verified = True
        self.user.save(update_fields=['is_verified'])
        
        return self.user


class PasswordReset(models.Model):
    """
    Model to store password reset tokens.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)
    requested_ip = models.CharField(max_length=45, null=True, blank=True)
    
    class Meta:
        db_table = 'password_reset'
        verbose_name = 'Password Reset'
        verbose_name_plural = 'Password Resets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        status = "used" if self.is_used else "pending"
        return f"{self.user.email} password reset ({status})"
    
    def is_valid(self):
        """Check if token is valid (not expired, not used)."""
        return not self.is_used and timezone.now() < self.expires_at
    
    def use(self):
        """Mark token as used."""
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_at'])


class AuditLog(models.Model):
    """
    Model to track important actions for security and compliance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'audit_log'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]
    
    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username}: {self.action} on {self.entity_type}"
    
    @classmethod
    def log(cls, action, entity_type, entity_id=None, user=None, ip_address=None, user_agent=None, details=None):
        """Create an audit log entry."""
        log_entry = cls(
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
        log_entry.save()
        return log_entry


class RateLimit(models.Model):
    """
    Model to track API rate limiting.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='rate_limits')
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    endpoint = models.CharField(max_length=255)
    request_count = models.IntegerField(default=1)
    first_request = models.DateTimeField(default=timezone.now)
    last_request = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'rate_limit'
        verbose_name = 'Rate Limit'
        verbose_name_plural = 'Rate Limits'
        indexes = [
            models.Index(fields=['ip_address', 'endpoint']),
            models.Index(fields=['user', 'endpoint']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        identifier = self.user.username if self.user else self.ip_address
        return f"{identifier}: {self.endpoint} ({self.request_count} requests)"
    
    def increment(self):
        """Increment the request count."""
        self.request_count += 1
        self.last_request = timezone.now()
        self.save(update_fields=['request_count', 'last_request'])
    
    def is_exceeded(self, limit):
        """Check if the rate limit is exceeded."""
        return self.request_count >= limit
    
    @classmethod
    def get_or_create(cls, endpoint, user=None, ip_address=None, window_minutes=1):
        """Get or create a rate limit entry with expiration window."""
        now = timezone.now()
        expires_at = now + timezone.timedelta(minutes=window_minutes)
        
        # Try to get an existing entry that hasn't expired
        if user:
            try:
                return cls.objects.get(
                    user=user,
                    endpoint=endpoint,
                    expires_at__gt=now
                )
            except cls.DoesNotExist:
                # Create a new entry
                return cls.objects.create(
                    user=user,
                    endpoint=endpoint,
                    expires_at=expires_at
                )
        elif ip_address:
            try:
                return cls.objects.get(
                    ip_address=ip_address,
                    endpoint=endpoint,
                    expires_at__gt=now
                )
            except cls.DoesNotExist:
                # Create a new entry
                return cls.objects.create(
                    ip_address=ip_address,
                    endpoint=endpoint,
                    expires_at=expires_at
                )
        else:
            raise ValueError("Either user or ip_address must be provided")
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired rate limit entries."""
        return cls.objects.filter(expires_at__lt=timezone.now()).delete()
