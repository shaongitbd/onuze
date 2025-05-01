import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist


class CommentConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time comment updates.
    Allows users to receive new comments on a post in real-time.
    """
    
    async def connect(self):
        """
        Connect to the WebSocket and join the post's comment group.
        """
        # Get post_id from the URL
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.group_name = f"comments_{self.post_id}"
        
        # Validate that the post exists
        post_exists = await self.check_post_exists()
        if not post_exists:
            await self.close()
            return
        
        # Join the post's comment group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        Leave the comment group when disconnecting.
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
    
    async def new_comment(self, event):
        """
        Receive new comment notification from channel layer and forward to WebSocket.
        """
        # Forward the new comment to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'comment_data': event.get('comment_data')
        }))
    
    async def comment_update(self, event):
        """
        Receive comment update from channel layer and forward to WebSocket.
        """
        # Forward the comment update to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'comment_update',
            'comment_id': event.get('comment_id'),
            'content': event.get('content'),
            'is_edited': event.get('is_edited')
        }))
    
    async def comment_delete(self, event):
        """
        Receive comment deletion notification from channel layer and forward to WebSocket.
        """
        # Forward the comment deletion to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'comment_delete',
            'comment_id': event.get('comment_id')
        }))
    
    async def vote_update(self, event):
        """
        Receive vote update from channel layer and forward to WebSocket.
        """
        # Forward the vote update to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'vote_update',
            'comment_id': event.get('comment_id'),
            'upvotes': event.get('upvotes'),
            'downvotes': event.get('downvotes'),
            'score': event.get('score')
        }))
    
    @database_sync_to_async
    def check_post_exists(self):
        """
        Check if the post exists.
        """
        from posts.models import Post
        try:
            Post.objects.get(id=self.post_id)
            return True
        except ObjectDoesNotExist:
            return False 