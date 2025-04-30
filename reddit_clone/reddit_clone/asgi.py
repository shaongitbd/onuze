"""
ASGI config for reddit_clone project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reddit_clone.settings')

# Initialize Django
django.setup()

# Import WebSocket consumers here to avoid circular imports
from notifications.consumers import NotificationConsumer, WebSocketSecurityMiddlewareStack
from posts.consumers import PostConsumer
from comments.consumers import CommentConsumer

# URL patterns for WebSockets
# Apply the security middleware stack to each consumer individually
websocket_urlpatterns = [
    path('ws/notifications/', WebSocketSecurityMiddlewareStack(NotificationConsumer.as_asgi())),
    path('ws/posts/<uuid:post_id>/', WebSocketSecurityMiddlewareStack(PostConsumer.as_asgi())),
    # Use SessionMiddlewareStack for comments to allow anonymous access
    path('ws/comments/<uuid:post_id>/', AllowedHostsOriginValidator(
        SessionMiddlewareStack(CommentConsumer.as_asgi())
    )),
]

# Configure ASGI application
application = ProtocolTypeRouter({
    # Django's ASGI application handles HTTP requests
    'http': get_asgi_application(),
    
    # WebSocket handling with enhanced security & origin validation
    'websocket': AllowedHostsOriginValidator(
        URLRouter(websocket_urlpatterns)
    ),
})
