from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from .models import AuditLog, RefreshToken as RefreshTokenModel


class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns access and refresh tokens stored in HttpOnly cookies.
    """
    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200:
            # Get tokens from response data
            access_token = response.data.get('access', None)
            refresh_token = response.data.get('refresh', None)
            
            if access_token and refresh_token:
                # Store tokens in HttpOnly cookies
                self._set_token_cookies(response, access_token, refresh_token)
                
                # Remove tokens from response body
                response.data = {
                    'success': True,
                    'user': response.data.get('user', {})
                }
                
                # Log successful login
                user = request.user if request.user.is_authenticated else None
                if user:
                    AuditLog.log(
                        action='login_success',
                        entity_type='user',
                        entity_id=user.id,
                        user=user,
                        ip_address=self._get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        status='success'
                    )
                    
                    # Store the refresh token in the database for tracking/revocation
                    RefreshTokenModel.objects.create(
                        user=user,
                        token=refresh_token,
                        expires_at=timezone.now() + settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timezone.timedelta(days=7)),
                        issued_by_ip=self._get_client_ip(request)
                    )
        
        return super().finalize_response(request, response, *args, **kwargs)
    
    def _set_token_cookies(self, response, access_token, refresh_token):
        """
        Set the JWT tokens as HttpOnly cookies.
        """
        # Get cookie settings
        cookie_secure = not settings.DEBUG  # True in production
        cookie_samesite = 'Lax' if settings.DEBUG else 'Strict'
        cookie_domain = settings.SESSION_COOKIE_DOMAIN
        cookie_path = settings.SESSION_COOKIE_PATH
        
        # Calculate expiration times (match token lifetimes)
        access_expiration = datetime.now() + settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timezone.timedelta(minutes=5))
        refresh_expiration = datetime.now() + settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timezone.timedelta(days=7))
        
        # Set cookies
        response.set_cookie(
            'access_token',
            access_token,
            expires=access_expiration,
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            domain=cookie_domain,
            path=cookie_path
        )
        
        response.set_cookie(
            'refresh_token',
            refresh_token,
            expires=refresh_expiration,
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            domain=cookie_domain,
            path=cookie_path
        )
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CookieTokenRefreshView(TokenRefreshView):
    """
    Refresh JWT tokens using the refresh token from the cookie.
    """
    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token', None)
        
        # If no token in cookie, check body (fallback)
        if not refresh_token:
            return super().post(request, *args, **kwargs)
        
        # Add to request data
        request.data['refresh'] = refresh_token
        
        # Standard refresh logic
        return super().post(request, *args, **kwargs)
    
    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200:
            # Get new tokens from response
            access_token = response.data.get('access', None)
            refresh_token = response.data.get('refresh', None)
            
            if access_token:
                # Update access token cookie
                self._set_token_cookies(response, access_token, refresh_token)
                
                # Remove tokens from response body
                response.data = {'success': True}
                
                # If there's a refresh token, update it in the database
                if refresh_token and hasattr(request, 'user') and request.user.is_authenticated:
                    try:
                        # Find the old token
                        old_token = request.COOKIES.get('refresh_token', None)
                        
                        if old_token:
                            # Mark old token as revoked
                            old_token_obj = RefreshTokenModel.objects.filter(token=old_token, revoked=False).first()
                            if old_token_obj:
                                old_token_obj.revoke()
                        
                        # Create a new token record
                        RefreshTokenModel.objects.create(
                            user=request.user,
                            token=refresh_token,
                            expires_at=timezone.now() + settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timezone.timedelta(days=7)),
                            issued_by_ip=self._get_client_ip(request)
                        )
                    except Exception:
                        pass  # Don't fail refresh if token recording fails
        
        return super().finalize_response(request, response, *args, **kwargs)
    
    def _set_token_cookies(self, response, access_token, refresh_token=None):
        """
        Set the JWT tokens as HttpOnly cookies.
        """
        # Get cookie settings
        cookie_secure = not settings.DEBUG  # True in production
        cookie_samesite = 'Lax' if settings.DEBUG else 'Strict'
        cookie_domain = settings.SESSION_COOKIE_DOMAIN
        cookie_path = settings.SESSION_COOKIE_PATH
        
        # Set access cookie
        access_expiration = datetime.now() + settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timezone.timedelta(minutes=5))
        response.set_cookie(
            'access_token',
            access_token,
            expires=access_expiration,
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            domain=cookie_domain,
            path=cookie_path
        )
        
        # Set refresh cookie if provided
        if refresh_token:
            refresh_expiration = datetime.now() + settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timezone.timedelta(days=7))
            response.set_cookie(
                'refresh_token',
                refresh_token,
                expires=refresh_expiration,
                httponly=True,
                secure=cookie_secure,
                samesite=cookie_samesite,
                domain=cookie_domain,
                path=cookie_path
            )
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CookieTokenLogoutView(APIView):
    """
    Logout view to clear JWT cookies and revoke refresh token.
    """
    def post(self, request, *args, **kwargs):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('refresh_token', None)
        
        # Log the logout attempt
        user = request.user if request.user.is_authenticated else None
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        if user:
            AuditLog.log(
                action='logout',
                entity_type='user',
                entity_id=user.id,
                user=user,
                ip_address=client_ip,
                user_agent=user_agent,
                status='success'
            )
        
        # Revoke the refresh token if it exists
        if refresh_token:
            try:
                token_obj = RefreshTokenModel.objects.filter(token=refresh_token, revoked=False).first()
                if token_obj:
                    token_obj.revoke()
            except Exception:
                pass  # Don't fail logout if token revocation fails
        
        # Create response and clear cookies
        response = Response({'success': True})
        self._clear_token_cookies(response)
        
        return response
    
    def _clear_token_cookies(self, response):
        """
        Clear JWT cookies.
        """
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
