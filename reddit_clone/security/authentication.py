from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import get_user_model
from django.utils import timezone
from .exceptions import AccountLocked, AccountBanned, VerificationRequired, TwoFactorRequired
from .models import RefreshToken, UserSession

User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that checks for account status.
    """
    def get_user(self, validated_token):
        """
        Attempt to find and return a user using the given validated token.
        Also checks if the account is locked, banned, or unverified.
        """
        try:
            user = super().get_user(validated_token)
            
            # Check if account is locked
            if user.is_account_locked():
                raise AccountLocked()
            
            # Check if account is banned
            if user.is_banned():
                raise AccountBanned(detail=f"Your account has been banned. Reason: {user.site_ban_reason}")
            
            # Check if account is verified
            if not user.is_verified and not user.is_staff:
                raise VerificationRequired()
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return user
            
        except TokenError as e:
            raise InvalidToken(e.args[0])


class TwoFactorAuthentication(BaseAuthentication):
    """
    Authentication class for two-factor authentication.
    Used after primary authentication to handle 2FA verification.
    """
    def authenticate(self, request):
        """
        Authenticate the request and return a tuple of (user, auth).
        """
        # This is meant to be used after JWT authentication
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        user = request.user
        
        # If 2FA is not enabled, authentication is complete
        if not user.two_factor_enabled:
            return (user, None)
        
        # Check if the request has a valid 2FA token
        token = request.META.get('HTTP_X_2FA_TOKEN')
        if not token:
            # Look for token in request data
            token = request.data.get('two_factor_code')
            if not token:
                # For GET requests, check query params
                token = request.query_params.get('two_factor_code')
        
        # If no token is provided, fail the authentication
        if not token:
            raise TwoFactorRequired()
        
        # Verify the 2FA token
        if not user.verify_2fa(token):
            # Record failed attempt
            user.record_failed_login()
            raise TwoFactorRequired(detail="Invalid two-factor authentication code.")
        
        # Reset failed login attempts on successful 2FA
        user.reset_failed_logins()
        
        # Create or update user session
        self._create_or_update_session(request, user)
        
        return (user, None)
    
    def _create_or_update_session(self, request, user):
        """
        Create or update a user session record.
        """
        # Get token from JWT auth
        auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()
        if len(auth_header) == 2 and auth_header[0].lower() == 'bearer':
            token = auth_header[1]
            
            # Get client info
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Try to find existing session
            try:
                session = UserSession.objects.get(
                    user=user,
                    token=token
                )
                # Update last activity
                session.update_activity()
            except UserSession.DoesNotExist:
                # Create new session
                expires_at = timezone.now() + timezone.timedelta(days=7)  # Match refresh token lifetime
                
                UserSession.objects.create(
                    user=user,
                    token=token,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    expires_at=expires_at,
                    device_info={
                        'ip': ip_address,
                        'user_agent': user_agent,
                        'platform': self._extract_platform(user_agent),
                        'browser': self._extract_browser(user_agent),
                    }
                )
    
    def _get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _extract_platform(self, user_agent):
        """
        Extract platform information from user agent string.
        """
        platforms = {
            'Windows': 'Windows',
            'Macintosh': 'Mac',
            'Linux': 'Linux',
            'Android': 'Android',
            'iOS': 'iOS',
            'iPhone': 'iOS',
            'iPad': 'iOS',
        }
        
        for key, value in platforms.items():
            if key in user_agent:
                return value
        
        return 'Unknown'
    
    def _extract_browser(self, user_agent):
        """
        Extract browser information from user agent string.
        """
        browsers = {
            'Chrome': 'Chrome',
            'Firefox': 'Firefox',
            'Safari': 'Safari',
            'Edge': 'Edge',
            'Opera': 'Opera',
            'MSIE': 'Internet Explorer',
            'Trident': 'Internet Explorer',
        }
        
        for key, value in browsers.items():
            if key in user_agent:
                return value
        
        return 'Unknown' 