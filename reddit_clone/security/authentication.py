from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import RefreshToken
from users.models import UserSession
from rest_framework.exceptions import AuthenticationFailed
from .exceptions import AccountLocked, AccountBanned, VerificationRequired, TwoFactorRequired

User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that checks for account status.
    Supports both bearer tokens and HttpOnly cookies.
    """
    def authenticate(self, request):
        """
        Try to authenticate the request using JWT from either:
        1. Authorization header (Bearer token)
        2. access_token cookie
        """
        # First try to authenticate using header (standard method)
        try:
            header_auth = super().authenticate(request)
            if header_auth is not None:
                return header_auth
        except Exception:
            pass  # Continue to cookie auth if header auth fails
            
        # If header auth fails, try cookie-based auth
        raw_token = request.COOKIES.get('access_token')
        
        if raw_token is None:
            return None
            
        # Validate token
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except Exception:
            return None
    
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
        This method should only proceed if a user has already been authenticated
        by a preceding authenticator (e.g., JWT or Session).
        """
        # Check if a user was authenticated by a *previous* authenticator.
        # Avoid accessing request.user directly here to prevent recursion.
        # Check the internal attributes set by DRF.
        user = getattr(request._request, '_user', None) # Access underlying HttpRequest
        if not user or not user.is_authenticated:
            # No user authenticated yet, or previous auth failed.
            # Let DRF continue with other authenticators or handle anonymous user.
            return None
        
        # --- At this point, user is authenticated by a primary method ---
        
        # If 2FA is not enabled for this user, authentication is complete.
        # The user object is already on the request, DRF will handle it.
        # Return None because *this* authenticator isn't adding anything new.
        if not getattr(user, 'two_factor_enabled', False):
            return None # Let DRF use the already authenticated user
        
        # Check if the user has already passed 2FA in this session/request
        # (e.g., via a flag set in the session or a temporary token)
        # Note: Requires SessionMiddleware to be active.
        if request.session.get('2fa_authenticated', False):
             # Already passed 2FA check for this session
             return None # Let DRF use the already authenticated user
             
        # --- 2FA is enabled, but not yet passed in this session ---
        
        # Check if a 2FA token is provided
        token = request.headers.get('X-2FA-Token') # Recommended header
        if not token:
            # Fallback: Check common POST/query parameter names
            token = request.data.get('two_factor_code') or \
                    request.query_params.get('two_factor_code') or \
                    request.data.get('two_factor_token') # Common alternative
        
        # If no token is provided where one is required, raise the specific exception.
        if not token:
            raise TwoFactorRequired("Two-factor authentication code required (X-2FA-Token header or form field).")
        
        # Verify the 2FA token
        try:
            if user.verify_totp_token(token): # Assuming verify_totp_token exists on user model
                # Token is valid. Mark 2FA as passed for this session.
                request.session['2fa_authenticated'] = True
                
                # Record successful login/2FA step if necessary (e.g., reset failed attempts)
                if hasattr(user, 'reset_failed_logins'):
                    user.reset_failed_logins()
                
                # Create or update user session for tracking active sessions
                self._create_or_update_session(request, user)
                
                # Return None, as the user object is already set on the request
                # by the preceding authenticator. DRF will use request.user.
                return None
            else:
                # Token is invalid
                if hasattr(user, 'record_failed_login'):
                    user.record_failed_login()
                raise AuthenticationFailed("Invalid two-factor authentication code.")
        except AttributeError as e:
             # Handle cases where user model might not have expected methods/attributes
             raise AuthenticationFailed(f"User model configuration error for 2FA: {e}")
        except Exception as e:
            # Catch other potential errors during token verification
            raise AuthenticationFailed(f"Error verifying two-factor token: {e}")

    def authenticate_header(self, request):
        """
        Return a string for the WWW-Authenticate header.
        Indicates that 2FA is required.
        """
        # This is usually triggered on 401 Unauthorized.
        # We rely on the TwoFactorRequired exception being caught by the handler
        # to signal the need for 2FA, but this can provide a hint.
        return 'Bearer realm="api", error="2fa_required", error_description="Two-factor authentication required."'

    def _create_or_update_session(self, request, user):
        """
        Create or update a user session record.
        """
        # Get token from JWT auth or cookie
        token = None
        auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()
        if len(auth_header) == 2 and auth_header[0].lower() == 'bearer':
            token = auth_header[1]
        else:
            # Try to get from cookie
            token = request.COOKIES.get('access_token')
            
        if not token:
            return
            
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