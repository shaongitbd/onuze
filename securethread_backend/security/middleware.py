from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import re

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    """
    def process_response(self, request, response):
        # Add security headers to the response
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'same-origin'
        response['Feature-Policy'] = "camera 'none'; microphone 'none'; geolocation 'none'"
        response['Permissions-Policy'] = "camera=(), microphone=(), geolocation=()"
        
        # Add CSP header based on settings
        csp_directives = getattr(settings, 'CSP_DIRECTIVES', None)
        if csp_directives:
            response['Content-Security-Policy'] = csp_directives
            
        return response

class JWTCookieMiddleware:
    """
    Middleware for WebSocket JWT authentication.
    This middleware extracts the JWT token from:
    1. The query string (token parameter)
    2. Cookies (access_token)
    Then authenticates the user and sets them in the scope.
    """
    def __init__(self, inner):
        self.inner = inner
    
    async def __call__(self, scope, receive, send):
        # Only process WebSocket connections
        if scope["type"] != "websocket":
            return await self.inner(scope, receive, send)
        
        # Try to get token from query string first
        query_string = scope.get("query_string", b"").decode()
        query_params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
        token = query_params.get("token")
        
        # If no token in query string, try cookies
        if not token:
            # Extract cookies from headers
            cookies = {}
            headers = dict(scope.get("headers", []))
            cookie_header = headers.get(b"cookie", b"").decode()
            
            if cookie_header:
                # Parse cookies
                for cookie in cookie_header.split("; "):
                    if "=" in cookie:
                        name, value = cookie.split("=", 1)
                        cookies[name] = value
            
            # Check for JWT token in cookies
            token = cookies.get("access_token")
        
        # Authenticate user with token if found
        if token:
            # If token starts with "JWT ", strip it
            if token.startswith("JWT "):
                token = token[4:]
                
            user = await self.get_user_from_token(token)
            if user:
                # Set authenticated user in scope
                scope["user"] = user
                print(f"WebSocket authenticated for user: {user.username}")
            else:
                print("WebSocket authentication failed: Invalid token")
        else:
            print("WebSocket authentication failed: No token found")
            
        # Pass to the next middleware
        return await self.inner(scope, receive, send)
    
    async def get_user_from_token(self, token):
        """
        Authenticate user with JWT token.
        """
        from django.contrib.auth import get_user_model
        from django.db import close_old_connections
        from channels.db import database_sync_to_async
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        
        # Close old database connections
        close_old_connections()
        
        try:
            # Verify token and get user ID
            token_obj = AccessToken(token)
            user_id = token_obj['user_id']
            
            # Get user from database
            User = get_user_model()
            
            @database_sync_to_async
            def get_user(user_id):
                try:
                    user = User.objects.get(id=user_id)
                    # You can add additional checks here if needed
                    # e.g., check if user is active, not banned, etc.
                    return user
                except User.DoesNotExist:
                    return None
            
            user = await get_user(user_id)
            return user
        except TokenError:
            return None
        except Exception as e:
            print(f"Error authenticating WebSocket user: {e}")
            return None 