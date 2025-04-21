import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone


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
            await self.close()
            return
            
        # Get the user ID
        self.user_id = str(self.scope["user"].id)
        
        # Set group name for the user
        self.group_name = f"notifications_{self.user_id}"
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
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
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    success = await self.mark_notification_read(notification_id)
                    await self.send(text_data=json.dumps({
                        'type': 'notification_marked_read',
                        'notification_id': notification_id,
                        'success': success
                    }))
                    
            elif action == 'mark_all_read':
                count = await self.mark_all_notifications_read()
                await self.send(text_data=json.dumps({
                    'type': 'all_notifications_marked_read',
                    'count': count
                }))
                
        except json.JSONDecodeError:
            # Invalid JSON
            pass
    
    async def notification_message(self, event):
        """
        Receive notification from channel layer and forward to WebSocket.
        """
        notification = event.get('notification')
        
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': notification
        }))
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """
        Get all unread notifications for the user.
        """
        from .models import Notification
        from .serializers import NotificationSerializer
        
        user = self.scope["user"]
        notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')[:20]  # Limit to latest 20
        
        # Serialize notifications
        serializer = NotificationSerializer(notifications, many=True)
        return serializer.data
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """
        Mark a notification as read.
        """
        from .models import Notification
        
        user = self.scope["user"]
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.mark_as_read()
            return True
        except (ObjectDoesNotExist, ValueError):
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """
        Mark all notifications for the user as read.
        """
        from .models import Notification
        
        user = self.scope["user"]
        count = Notification.objects.filter(user=user, is_read=False).count()
        Notification.objects.filter(user=user, is_read=False).update(
            is_read=True, 
            read_at=timezone.now()
        )
        return count 