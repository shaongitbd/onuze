import json
import re
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from django.urls import path, re_path

from notifications.models import Notification
from notifications.consumers import NotificationConsumer, WebSocketSecurityMiddlewareStack

User = get_user_model()

class MockAuthMiddleware:
    """Mock auth middleware for testing authenticated WebSocket connections"""
    
    def __init__(self, inner, user=None):
        self.inner = inner
        self.user = user
        
    async def __call__(self, scope, receive, send):
        if self.user:
            scope['user'] = self.user
        return await self.inner(scope, receive, send)

def AuthMiddlewareStack(inner, user=None):
    return MockAuthMiddleware(inner, user)

class NotificationConsumerTests(TestCase):
    async def setUp(self):
        # Create a test user
        self.user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a banned user for testing ban checks
        self.banned_user = await database_sync_to_async(User.objects.create_user)(
            username='banneduser',
            email='banned@example.com',
            password='password123'
        )
        # Set is_banned method to return True for testing
        self.banned_user.is_banned = lambda: True
        
        # Create test notifications
        self.notification = await database_sync_to_async(Notification.objects.create)(
            user=self.user,
            notification_type='comment_reply',
            content_type='comment',
            is_read=False,
            title='New comment reply',
            message='Someone replied to your comment'
        )

    async def tearDown(self):
        await database_sync_to_async(Notification.objects.all().delete)()
        await database_sync_to_async(User.objects.all().delete)()

    def get_application(self, user=None):
        """Helper to create application with authenticated user"""
        return AuthMiddlewareStack(
            URLRouter([
                path('ws/notifications/', NotificationConsumer.as_asgi())
            ]),
            user=user
        )

    async def test_connect_authenticated(self):
        """Test connecting with authenticated user"""
        application = self.get_application(user=self.user)
        communicator = WebsocketCommunicator(application, '/ws/notifications/')
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive unread notifications upon connection
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'notification_list')
        self.assertIn('notifications', response)
        
        await communicator.disconnect()

    async def test_connect_unauthenticated(self):
        """Test connecting with unauthenticated user (should reject)"""
        application = self.get_application(user=None)  # No user
        communicator = WebsocketCommunicator(application, '/ws/notifications/')
        
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_connect_banned_user(self):
        """Test connecting with banned user (should reject)"""
        application = self.get_application(user=self.banned_user)
        communicator = WebsocketCommunicator(application, '/ws/notifications/')
        
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_mark_read_notification(self):
        """Test marking a notification as read"""
        # Mock the database function
        with patch('notifications.consumers.NotificationConsumer.mark_notification_read') as mock_mark_read:
            mock_mark_read.return_value = True
            
            application = self.get_application(user=self.user)
            communicator = WebsocketCommunicator(application, '/ws/notifications/')
            
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            
            # Skip initial notification list
            await communicator.receive_json_from()
            
            # Send mark_read action
            await communicator.send_json_to({
                'action': 'mark_read',
                'notification_id': str(self.notification.id)
            })
            
            # Verify response
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'notification_marked_read')
            self.assertEqual(response['notification_id'], str(self.notification.id))
            self.assertTrue(response['success'])
            
            await communicator.disconnect()

    async def test_mark_all_read(self):
        """Test marking all notifications as read"""
        # Mock the database function
        with patch('notifications.consumers.NotificationConsumer.mark_all_notifications_read') as mock_mark_all:
            mock_mark_all.return_value = 5  # 5 notifications marked as read
            
            application = self.get_application(user=self.user)
            communicator = WebsocketCommunicator(application, '/ws/notifications/')
            
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            
            # Skip initial notification list
            await communicator.receive_json_from()
            
            # Send mark_all_read action
            await communicator.send_json_to({
                'action': 'mark_all_read'
            })
            
            # Verify response
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'all_notifications_marked_read')
            self.assertEqual(response['count'], 5)
            
            await communicator.disconnect()

    async def test_invalid_action(self):
        """Test sending an invalid action"""
        application = self.get_application(user=self.user)
        communicator = WebsocketCommunicator(application, '/ws/notifications/')
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial notification list
        await communicator.receive_json_from()
        
        # Send invalid action
        await communicator.send_json_to({
            'action': 'invalid_action'
        })
        
        # Verify error response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertEqual(response['code'], 'unknown_action')
        
        await communicator.disconnect()

    async def test_invalid_json(self):
        """Test sending invalid JSON"""
        application = self.get_application(user=self.user)
        communicator = WebsocketCommunicator(application, '/ws/notifications/')
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial notification list
        await communicator.receive_json_from()
        
        # Send invalid JSON
        await communicator.send_to(text_data="not valid json")
        
        # Verify error response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'error')
        self.assertEqual(response['code'], 'invalid_format')
        
        await communicator.disconnect()

    async def test_receive_notification(self):
        """Test receiving a notification through the channel layer"""
        application = self.get_application(user=self.user)
        communicator = WebsocketCommunicator(application, '/ws/notifications/')
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial notification list
        await communicator.receive_json_from()
        
        # Create notification data
        notification_data = {
            'id': str(self.notification.id),
            'title': 'New notification',
            'message': 'This is a test notification',
            'notification_type': 'test',
            'created_at': timezone.now().isoformat()
        }
        
        # Send notification message directly (simulating channel layer)
        await communicator.send_json_to({
            'type': 'notification_message',
            'notification': notification_data
        })
        
        # Verify notification is forwarded to WebSocket
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'new_notification')
        self.assertEqual(response['notification'], notification_data)
        
        await communicator.disconnect()

    @patch('notifications.consumers.NotificationConsumer.sanitize_string')
    async def test_string_sanitization(self, mock_sanitize):
        """Test that input sanitization is called"""
        mock_sanitize.side_effect = lambda x: x  # Pass-through for testing
        
        application = self.get_application(user=self.user)
        communicator = WebsocketCommunicator(application, '/ws/notifications/')
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial notification list
        await communicator.receive_json_from()
        
        # Send an action that should be sanitized
        await communicator.send_json_to({
            'action': 'mark_read',
            'notification_id': '12345'
        })
        
        # Wait for any response
        await communicator.receive_json_from()
        
        # Verify sanitize was called on the action
        mock_sanitize.assert_any_call('mark_read')
        
        await communicator.disconnect()

    async def test_actual_sanitize_string(self):
        """Test the actual sanitize_string function"""
        consumer = NotificationConsumer()
        
        # Test sanitizing some potentially dangerous strings
        test_cases = [
            ("<script>alert('xss')</script>", "scriptalert('xss')/script"),
            ("normal text", "normal text"),
            ('Single quote\'s', "Single quotes"),
            ('Double "quotes"', 'Double quotes')
        ]
        
        for input_str, expected in test_cases:
            sanitized = consumer.sanitize_string(input_str)
            # Check that dangerous characters were removed
            self.assertFalse(any(char in sanitized for char in ['<', '>', '&', "'", '"']))
            # Self-test to make sure our assertion makes sense
            self.assertTrue(all(char not in expected for char in ['<', '>', '&', "'", '"']))

    async def test_message_size_limit(self):
        """Test that large messages are rejected"""
        application = self.get_application(user=self.user)
        communicator = WebsocketCommunicator(application, '/ws/notifications/')
        
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial notification list
        await communicator.receive_json_from()
        
        # Send a message that exceeds the size limit (8KB)
        large_message = json.dumps({
            'action': 'mark_read',
            'notification_id': 'a' * 10000  # Much larger than 8KB
        })
        
        # This send should be ignored due to size
        await communicator.send_to(text_data=large_message)
        
        # Try to receive - should timeout because no response is sent for oversized messages
        with self.assertRaises(TimeoutError):
            await communicator.receive_from(timeout=0.5)
            
        await communicator.disconnect() 