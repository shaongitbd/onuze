import uuid
import pyotp
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.mail import send_mail


class UserManager(BaseUserManager):
    """
    Custom manager for the User model.
    """
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model that uses email for authentication and stores additional user info.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)
    avatar = models.CharField(max_length=255, blank=True, null=True)
    karma = models.IntegerField(default=0)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True, null=True)
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    is_site_banned = models.BooleanField(default=False)
    site_ban_reason = models.TextField(null=True, blank=True)
    site_banned_until = models.DateTimeField(null=True, blank=True)
    site_banned_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='site_banned_users'
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)
    
    def increment_karma(self, amount=1):
        """Increment user's karma score."""
        self.karma += amount
        self.save(update_fields=['karma'])
    
    def decrement_karma(self, amount=1):
        """Decrement user's karma score."""
        self.karma -= amount
        self.save(update_fields=['karma'])
    
    def lock_account(self, duration_hours=24):
        """Lock user account for specified duration."""
        self.account_locked_until = timezone.now() + timezone.timedelta(hours=duration_hours)
        self.save(update_fields=['account_locked_until'])
    
    def unlock_account(self):
        """Unlock user account."""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
    
    def is_account_locked(self):
        """Check if user account is locked."""
        if not self.account_locked_until:
            return False
        return timezone.now() < self.account_locked_until
    
    def record_failed_login(self):
        """Record a failed login attempt."""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'last_failed_login'])
        
        # Automatically lock account after too many failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account()
    
    def reset_failed_logins(self):
        """Reset failed login counter."""
        self.failed_login_attempts = 0
        self.save(update_fields=['failed_login_attempts'])
    
    def apply_site_ban(self, reason, banned_by, duration_days=None):
        """Ban user from the site."""
        self.is_site_banned = True
        self.site_ban_reason = reason
        self.site_banned_by = banned_by
        
        if duration_days:
            self.site_banned_until = timezone.now() + timezone.timedelta(days=duration_days)
        
        self.save(update_fields=[
            'is_site_banned', 
            'site_ban_reason', 
            'site_banned_by',
            'site_banned_until'
        ])
    
    def remove_site_ban(self):
        """Remove site ban from user."""
        self.is_site_banned = False
        self.site_banned_until = None
        self.save(update_fields=['is_site_banned', 'site_banned_until'])
    
    def is_banned(self):
        """Check if user is banned from the site."""
        if not self.is_site_banned:
            return False
        
        # If there's an end date and it's in the past, unban automatically
        if self.site_banned_until and timezone.now() > self.site_banned_until:
            self.remove_site_ban()
            return False
            
        return True

    def verify_2fa(self, code):
        """
        Verify a 2FA code against the user's secret.
        """
        if not self.two_factor_secret:
            return False
        
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(code)
    
    def generate_2fa_secret(self):
        """
        Generate a new 2FA secret for the user.
        """
        self.two_factor_secret = pyotp.random_base32()
        self.save(update_fields=['two_factor_secret'])
        return self.two_factor_secret
    
    def get_2fa_qr_uri(self, issuer_name="Reddit Clone"):
        """
        Get the URI for generating a QR code for 2FA setup.
        """
        if not self.two_factor_secret:
            self.generate_2fa_secret()
        
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.provisioning_uri(name=self.email, issuer_name=issuer_name)


class Role(models.Model):
    """
    Role model for user permissions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()

    class Meta:
        db_table = 'role'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.name


class UserRole(models.Model):
    """
    Many-to-many relationship between users and roles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_roles')

    class Meta:
        db_table = 'user_role'
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class UserBlock(models.Model):
    """
    Model to track when a user blocks another user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocking')
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(default=timezone.now)
    reason = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'user_block'
        verbose_name = 'User Block'
        verbose_name_plural = 'User Blocks'
        unique_together = ('user', 'blocked_user')

    def __str__(self):
        return f"{self.user.username} blocked {self.blocked_user.username}"


class UserSession(models.Model):
    """
    Model to track user sessions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=255, unique=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    device_info = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'user_session'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

    def is_valid(self):
        """Check if session is still valid."""
        return timezone.now() < self.expires_at

    def update_activity(self):
        """Update the last activity time."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
