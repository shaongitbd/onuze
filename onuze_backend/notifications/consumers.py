import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.utils import timezone
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
import logging
from django.conf import settings
from .models import Notification
from .serializers import NotificationSerializer
from security.models import AuditLog
from security.middleware import JWTCookieMiddleware

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseMiddleware):
    """
    Custom middleware for WebSocket rate limiting.
    Limits the number of connections and messages per user.
    """
    def __init__(self, inner):
        super().__init__(inner)
        self.connections = {}  # Store active connections per user
        self.message_counts = {}  # Store message counts per connection
        self.MAX_CONNECTIONS_PER_USER = 5
        self.MAX_MESSAGES_PER_MINUTE = 60
    
    async def __call__(self, scope, receive, send):
        # Get user from scope
        if scope["user"].is_authenticated:
            user_id = str(scope["user"].id)
            
            # Check connection count for this user
            if user_id not in self.connections:
                self.connections[user_id] = 0
            
            if scope["type"] == "websocket.connect":
                # Allow staff to have unlimited connections
                if not scope["user"].is_staff and self.connections[user_id] >= self.MAX_CONNECTIONS_PER_USER:
                    # Too many connections, reject
                    logger.warning(f"WebSocket connection rejected: Too many connections for user {user_id}")
                    return None
                
                self.connections[user_id] += 1
                
                # Custom receive that tracks message rates
                original_receive = receive
                connection_id = f"{user_id}_{id(receive)}"
                self.message_counts[connection_id] = {
                    "count": 0,
                    "reset_at": timezone.now() + timezone.timedelta(minutes=1)
                }
                
                async def rate_limited_receive():
                    message = await original_receive()
                    
                    if message["type"] == "websocket.receive":
                        # Check if we need to reset the counter
                        now = timezone.now()
                        if now > self.message_counts[connection_id]["reset_at"]:
                            self.message_counts[connection_id] = {
                                "count": 0,
                                "reset_at": now + timezone.timedelta(minutes=1)
                            }
                        
                        # Check rate limit
                        self.message_counts[connection_id]["count"] += 1
                        if (not scope["user"].is_staff and 
                            self.message_counts[connection_id]["count"] > self.MAX_MESSAGES_PER_MINUTE):
                            # Rate limit exceeded
                            logger.warning(f"WebSocket message rejected: Rate limit exceeded for user {user_id}")
                            return {"type": "websocket.close", "code": 1008}  # Policy violation
                    
                    return message
                
                # Store original disconnect to clean up our tracking
                original_disconnect = scope.get("websocket_disconnect", None)
                
                async def clean_up_disconnect(message):
                    # Decrement the connection count on disconnect
                    self.connections[user_id] -= 1
                    if connection_id in self.message_counts:
                        del self.message_counts[connection_id]
                    
                    # Call original handler if it exists
                    if original_disconnect:
                        await original_disconnect(message)
                
                # Replace receive with rate limited version
                scope["_rate_limited_receive"] = rate_limited_receive
                scope["websocket_disconnect"] = clean_up_disconnect
                
                # Override receive function
                async def wrapped_receive():
                    if hasattr(scope, "_rate_limited_receive"):
                        return await scope["_rate_limited_receive"]()
                    return await original_receive()
                
                return await self.inner(scope, wrapped_receive, send)
            
            # For all other message types, just pass through
            return await self.inner(scope, receive, send)
        
        # User not authenticated, pass through
        return await self.inner(scope, receive, send)


class CSRFProtectionMiddleware(BaseMiddleware):
    """
    Middleware for CSRF protection in WebSockets.
    Validates the Origin header against allowed origins.
    """
    def __init__(self, inner):
        super().__init__(inner)
        self.allowed_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
        if not self.allowed_origins and getattr(settings, 'CORS_ALLOWED_ORIGINS', None):
            self.allowed_origins = settings.CORS_ALLOWED_ORIGINS
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            # Get the Origin header
            origin = None
            for name, value in scope.get("headers", []):
                if name == b"origin":
                    origin = value.decode("latin1")
                    break
            
            # Validate the Origin
            if origin:
                valid_origin = False
                for allowed in self.allowed_origins:
                    if origin == allowed or origin.startswith(allowed):
                        valid_origin = True
                        break
                
                if not valid_origin:
                    logger.warning(f"WebSocket connection rejected: Invalid origin {origin}")
                    return None
            else:
                # No Origin header, this is suspicious
                logger.warning("WebSocket connection rejected: Missing Origin header")
                return None
        
        return await self.inner(scope, receive, send)


def WebSocketSecurityMiddlewareStack(inner):
    """
    Combine the security middlewares for WebSockets.
    """
    # JWTCookieMiddleware handles authentication, so we don't need AuthMiddlewareStack
    from security.middleware import JWTCookieMiddleware
    
    return JWTCookieMiddleware(
        RateLimitMiddleware(
            CSRFProtectionMiddleware(inner)
        )
    )


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    Allows users to receive new notifications instantly.
    """
    
    async def connect(self):
        """
        Connect to the WebSocket and add user to their notification group.
        """
        # Check authentication
        if self.scope["user"].is_anonymous:
            # Reject the connection if user is not authenticated
            logger.warning(f"WebSocket connection rejected: User not authenticated")
            await self.close(code=4003)  # 4003 = Not authenticated
            return
            
        # Get the user ID
        self.user_id = str(self.scope["user"].id)
        
        # Check if user is banned
        is_banned = await self.is_user_banned()
        if is_banned:
            logger.warning(f"WebSocket connection rejected: User {self.user_id} is banned")
            await self.close(code=4004)  # 4004 = User banned
            return
            
        # Set group name for the user
        self.group_name = f"notifications_{self.user_id}"
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Log successful connection
        logger.info(f"WebSocket connection established for user {self.user_id}")
        
        # Accept the connection
        await self.accept()
        
        # Send all unread notifications on connect
        unread_notifications = await self.get_unread_notifications()
        if unread_notifications:
            await self.send(text_data=json.dumps({
                'type': 'notification_list',
                'notifications': unread_notifications
            }))
    
    async def disconnect(self, close_code):
        """
        Leave the notification group when disconnecting.
        """
        if hasattr(self, 'user_id'):
            logger.info(f"WebSocket connection closed for user {self.user_id} with code {close_code}")
            
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Handle messages from WebSocket.
        """
        try:
            # Validate message size
            if len(text_data) > 8192:  # 8KB limit
                logger.warning(f"WebSocket message rejected: Message too large from user {self.user_id}")
                return
                
            # Parse JSON data
            data = json.loads(text_data)
            
            # Validate message schema
            if not isinstance(data, dict):
                logger.warning(f"WebSocket message rejected: Invalid message format from user {self.user_id}")
                return
                
            action = data.get('action')
            
            # Validate action
            if not action or not isinstance(action, str):
                logger.warning(f"WebSocket message rejected: Missing action from user {self.user_id}")
                return
            
            # Sanitize inputs to prevent injection
            action = self.sanitize_string(action)
            
            # Handle different actions
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                if not notification_id or not isinstance(notification_id, str):
                    logger.warning(f"WebSocket message rejected: Invalid notification_id from user {self.user_id}")
                    return
                    
                # Sanitize and validate notification_id
                notification_id = self.sanitize_string(notification_id)
                
                # UUID validation pattern
                uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
                if not uuid_pattern.match(notification_id):
                    logger.warning(f"WebSocket message rejected: Invalid notification_id format from user {self.user_id}")
                    return
                
                try:
                    success = await self.mark_notification_read(notification_id)
                    await self.send(text_data=json.dumps({
                        'type': 'notification_marked_read',
                        'notification_id': notification_id,
                        'success': success
                    }))
                except PermissionDenied:
                    logger.warning(f"WebSocket action denied: User {self.user_id} tried to mark notification {notification_id} as read without permission")
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'code': 'permission_denied',
                        'message': 'You do not have permission to perform this action'
                    }))
                    
            elif action == 'mark_all_read':
                try:
                    count = await self.mark_all_notifications_read()
                    await self.send(text_data=json.dumps({
                        'type': 'all_notifications_marked_read',
                        'count': count
                    }))
                except PermissionDenied:
                    logger.warning(f"WebSocket action denied: User {self.user_id} tried to mark all notifications as read without permission")
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'code': 'permission_denied',
                        'message': 'You do not have permission to perform this action'
                    }))
            else:
                logger.warning(f"WebSocket message rejected: Unknown action '{action}' from user {self.user_id}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'code': 'unknown_action',
                    'message': 'Unknown action'
                }))
                
        except json.JSONDecodeError:
            # Invalid JSON
            logger.warning(f"WebSocket message rejected: Invalid JSON from user {self.user_id}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'code': 'invalid_format',
                'message': 'Invalid message format'
            }))
        except Exception as e:
            # Log unexpected errors
            logger.error(f"WebSocket error for user {self.user_id}: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'code': 'server_error',
                'message': 'An unexpected error occurred'
            }))
    
    async def notification_message(self, event):
        """
        Receive notification from channel layer and forward to WebSocket.
        """
        notification = event.get('notification')
        
        # Debug logging
        print(f"WebSocket notification_message received in consumer for user {self.user_id}")
        print(f"Notification data: {notification}")
        
        try:
            # Send notification to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'new_notification',
                'notification': notification
            }))
            print(f"WebSocket notification successfully sent to client for user {self.user_id}")
        except Exception as e:
            print(f"Error sending WebSocket notification to client: {e}")
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """
        Get all unread notifications for the user.
        """
        notifications = Notification.objects.filter(
            user=self.scope["user"],
            is_read=False
        ).order_by('-created_at')[:20]  # Limit to latest 20
        
        # Log access
        logger.info(f"User {self.user_id} retrieved {len(notifications)} unread notifications")
        
        # Serialize notifications
        serializer = NotificationSerializer(notifications, many=True)
        return serializer.data
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """
        Mark a notification as read.
        """
        user = self.scope["user"]
        try:
            notification = Notification.objects.get(id=notification_id)
            
            # Ensure the notification belongs to the user
            if notification.user.id != user.id:
                logger.warning(f"Permission denied: User {user.id} tried to mark notification {notification_id} belonging to user {notification.user.id} as read")
                raise PermissionDenied("You do not have permission to mark this notification as read")
                
            notification.mark_as_read()
            
            # Log the action
            AuditLog.log(
                action='notification_mark_read',
                entity_type='notification',
                entity_id=notification.id,
                user=user,
                details={
                    'notification_type': notification.notification_type,
                    'content_type': notification.content_type
                },
                status='success'
            )
            
            return True
        except ObjectDoesNotExist:
            logger.warning(f"Notification not found: User {user.id} tried to mark non-existent notification {notification_id} as read")
            return False
        except PermissionDenied as e:
            raise e
        except (ValueError, ValidationError) as e:
            logger.warning(f"Invalid notification request: {str(e)}")
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """
        Mark all notifications for the user as read.
        """
        user = self.scope["user"]
        count = Notification.objects.filter(user=user, is_read=False).count()
        
        if count > 0:
            Notification.objects.filter(user=user, is_read=False).update(
                is_read=True, 
                read_at=timezone.now()
            )
            
            # Log the action
            AuditLog.log(
                action='notification_mark_all_read',
                entity_type='user',
                entity_id=user.id,
                user=user,
                details={'count': count},
                status='success'
            )
            
            logger.info(f"User {user.id} marked {count} notifications as read")
        
        return count
    
    @database_sync_to_async
    def is_user_banned(self):
        """
        Check if the user is banned.
        """
        user = self.scope["user"]
        return user.is_banned() if hasattr(user, 'is_banned') else False
    
    def sanitize_string(self, value):
        """
        Sanitize input strings to prevent injection attacks.
        """
        if not isinstance(value, str):
            return value
            
        # Replace special characters
        return re.sub(r'[<>&\'"]', '', value) 