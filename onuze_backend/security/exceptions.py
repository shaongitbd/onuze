from rest_framework.exceptions import APIException, AuthenticationFailed, NotAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from security.models import AuditLog

class RateLimitExceeded(APIException):
    """
    Custom exception for rate limiting.
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _('Request rate limit exceeded.')
    default_code = 'rate_limit_exceeded'


class AccountLocked(APIException):
    """
    Custom exception for locked accounts.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Your account has been temporarily locked due to too many failed login attempts.')
    default_code = 'account_locked'


class AccountBanned(APIException):
    """
    Custom exception for banned accounts.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Your account has been banned.')
    default_code = 'account_banned'


class InvalidToken(AuthenticationFailed):
    """
    Custom exception for invalid tokens.
    """
    default_detail = _('Token is invalid or expired.')
    default_code = 'invalid_token'


class VerificationRequired(AuthenticationFailed):
    """
    Custom exception for unverified accounts.
    """
    default_detail = _('Account is not verified. Please check your email for verification instructions.')
    default_code = 'verification_required'


class TwoFactorRequired(AuthenticationFailed):
    """
    Custom exception for 2FA requirement.
    """
    default_detail = _('Two-factor authentication code required.')
    default_code = 'two_factor_required'


class InvalidTwoFactorCode(AuthenticationFailed):
    """
    Custom exception for invalid 2FA codes.
    """
    default_detail = _('Invalid two-factor authentication code.')
    default_code = 'invalid_two_factor_code'


def custom_exception_handler(exc, context):
    """
    Custom exception handler for better security exception handling.
    """
    # Import exception_handler here to avoid circular imports
    from rest_framework.views import exception_handler
   
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If this is a custom security exception, log it
    if isinstance(exc, (
        RateLimitExceeded, AccountLocked, AccountBanned,
        InvalidToken, VerificationRequired, TwoFactorRequired, 
        InvalidTwoFactorCode
    )):
        try:
            # Log the security exception
            request = context.get('request')
            if request and hasattr(request, 'user'):
                user = request.user
                
                AuditLog.log(
                    action=f"security_exception_{exc.default_code}",
                    entity_type='user',
                    entity_id=user.id if user.is_authenticated else None,
                    user=user if user.is_authenticated else None,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={
                        'exception': exc.__class__.__name__,
                        'detail': str(exc.detail),
                        'code': exc.default_code,
                        'path': request.path,
                        'method': request.method,
                    }
                )
        except Exception:
            # Don't let logging errors affect the response
            pass
    
    # For all exceptions, create a standardized response format
    if response is not None:
        # Create a standardized error structure
        standardized_data = {
            'timestamp': timezone.now().isoformat(),
            'status_code': response.status_code,
            'success': False
        }
        
        # Format error message in a clean way
        if isinstance(response.data, list):
            # Convert list errors to a string joined with "; "
            standardized_data['detail'] = "; ".join(response.data)
        elif isinstance(response.data, dict):
            # Check if it's a field error dictionary
            if any(isinstance(value, list) and value for value in response.data.values()):
                # Get the first field error
                for field, errors in response.data.items():
                    if errors and isinstance(errors, list):
                        # Just show the error message without the field name
                        standardized_data['detail'] = errors[0]
                        break
            # If it's a simple dict with just 'detail' key and string value, extract it
            elif 'detail' in response.data and isinstance(response.data['detail'], str):
                standardized_data['detail'] = response.data['detail']
            else:
                # For complex dictionaries, redact sensitive data
                if 'detail' in response.data and isinstance(response.data['detail'], dict):
                    for key in list(response.data['detail'].keys()):
                        if key in ['token', 'password', 'refresh', 'access']:
                            response.data['detail'][key] = ['[Redacted]']
                
                # Fall back to the original structure if we can't simplify
                standardized_data['detail'] = response.data
        else:
            # For any other type, convert to string
            standardized_data['detail'] = str(response.data)
        
        # Add trace ID for tracking (don't include in production)
        if hasattr(context.get('request', None), 'trace_id'):
            standardized_data['trace_id'] = context['request'].trace_id
        
        # Replace the original data with our standardized structure
        response.data = standardized_data
    
    return response


def get_client_ip(request):
    """
    Get the client IP address from the request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip 