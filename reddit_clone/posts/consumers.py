import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .models import Post
from users.models import Activity


class PostConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time post updates.
    Allows users to receive vote count updates and new comments.
    """
    
    async def connect(self):
        """
        Connect to the WebSocket and join the post group.
        """
        # Get post_id from the URL
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.group_name = f"post_{self.post_id}"
        
        # Validate that the post exists
        post_exists = await self.check_post_exists()
        if not post_exists:
            await self.close()
            return
        
        # Join the post group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        Leave the post group when disconnecting.
        """
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Handle messages from WebSocket.
        Currently unused but kept for potential future use.
        """
        pass  # No action needed for now
    
    async def post_update(self, event):
        """
        Receive post update from channel layer and forward to WebSocket.
        """
        # Forward the update to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'post_update',
            'post_data': event.get('post_data')
        }))
    
    async def new_comment(self, event):
        """
        Receive new comment notification from channel layer and forward to WebSocket.
        """
        # Forward the new comment to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'comment_data': event.get('comment_data')
        }))
    
    async def vote_update(self, event):
        """
        Receive vote update from channel layer and forward to WebSocket.
        """
        # Forward the vote update to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'vote_update',
            'upvotes': event.get('upvotes'),
            'downvotes': event.get('downvotes'),
            'score': event.get('score')
        }))
    
    @database_sync_to_async
    def check_post_exists(self):
        """
        Check if the post exists.
        """
        try:
            Post.objects.get(id=self.post_id)
            return True
        except ObjectDoesNotExist:
            return False 