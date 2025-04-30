import json
from unittest.mock import patch, MagicMock, AsyncMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from django.urls import path

from notifications.consumers import (
    RateLimitMiddleware, 
    CSRFProtectionMiddleware,
    WebSocketSecurityMiddlewareStack
)

User = get_user_model()

class MockInner:
    """Mock inner application for middleware testing"""
    
    def __init__(self, connected=True, close_code=None):
        self.connected = connected
        self.close_code = close_code
        self.called = False
        self.scope = None
        self.receive = None
        self.send = None
        
    async def __call__(self, scope, receive, send):
        self.called = True
        self.scope = scope
        self.receive = receive
        self.send = send
        
        if not self.connected:
            return None
            
        if self.close_code:
            await send({"type": "websocket.close", "code": self.close_code})
        else:
            await send({"type": "websocket.accept"})
            
            # Handle one message to test receive
            message = await receive()
            if message["type"] == "websocket.receive":
                await send({
                    "type": "websocket.send",
                    "text": "Response: " + message.get("text", "")
                })

class RateLimitMiddlewareTests(TestCase):
    async def setUp(self):
        # Create test users
        self.user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        self.staff_user = await database_sync_to_async(User.objects.create_user)(
            username='staffuser',
            email='staff@example.com',
            password='password123',
            is_staff=True
        )

    async def tearDown(self):
        await database_sync_to_async(User.objects.all().delete)()

    async def test_connection_limit_regular_user(self):
        """Test that regular users are limited in number of connections"""
        middleware = RateLimitMiddleware(MockInner(connected=True))
        
        # Set up user connections counter artificially high
        middleware.connections[str(self.user.id)] = middleware.MAX_CONNECTIONS_PER_USER
        
        # Create a new scope with the user
        scope = {
            "type": "websocket.connect",
            "user": self.user
        }
        
        # This connection should be rejected
        result = await middleware(scope, AsyncMock(), AsyncMock())
        self.assertIsNone(result)

    async def test_connection_limit_staff_user(self):
        """Test that staff users bypass connection limits"""
        middleware = RateLimitMiddleware(MockInner(connected=True))
        
        # Set up user connections counter artificially high
        middleware.connections[str(self.staff_user.id)] = middleware.MAX_CONNECTIONS_PER_USER
        
        # Create a new scope with the staff user
        scope = {
            "type": "websocket.connect",
            "user": self.staff_user
        }
        
        # Staff user connection should be allowed despite limit
        await middleware(scope, AsyncMock(), AsyncMock())
        self.assertEqual(middleware.connections[str(self.staff_user.id)], 
                         middleware.MAX_CONNECTIONS_PER_USER + 1)

    async def test_message_rate_limit(self):
        """Test that message rate limiting works"""
        inner_mock = MockInner(connected=True)
        middleware = RateLimitMiddleware(inner_mock)
        
        # Create scope with regular user
        scope = {
            "type": "websocket.connect",
            "user": self.user
        }
        
        # Setup receive function that will simulate messages
        messages_received = []
        
        async def mock_receive():
            # First return a connect message
            if not messages_received:
                messages_received.append("connect")
                return {"type": "websocket.connect"}
                
            # Then return a series of receive messages
            messages_received.append("receive")
            return {"type": "websocket.receive", "text": "test message"}
        
        send_messages = []
        
        async def mock_send(message):
            send_messages.append(message)
            return None
        
        # Connect user
        await middleware(scope, mock_receive, mock_send)
        
        # Artificially set message count over limit
        connection_id = next(iter(middleware.message_counts.keys()))
        middleware.message_counts[connection_id]["count"] = middleware.MAX_MESSAGES_PER_MINUTE
        
        # Try to receive more messages (should hit rate limit)
        wrapped_receive = scope["_rate_limited_receive"]
        message = await wrapped_receive()
        
        # Should get a close message with code 1008 (policy violation)
        self.assertEqual(message["type"], "websocket.close")
        self.assertEqual(message["code"], 1008)

    async def test_staff_bypass_message_rate_limit(self):
        """Test that staff users bypass message rate limiting"""
        inner_mock = MockInner(connected=True)
        middleware = RateLimitMiddleware(inner_mock)
        
        # Create scope with staff user
        scope = {
            "type": "websocket.connect",
            "user": self.staff_user
        }
        
        # Setup receive function that will simulate messages
        messages_received = []
        
        async def mock_receive():
            # First return a connect message
            if not messages_received:
                messages_received.append("connect")
                return {"type": "websocket.connect"}
                
            # Then return a series of receive messages
            messages_received.append("receive")
            return {"type": "websocket.receive", "text": "test message"}
        
        send_messages = []
        
        async def mock_send(message):
            send_messages.append(message)
            return None
        
        # Connect staff user
        await middleware(scope, mock_receive, mock_send)
        
        # Artificially set message count over limit
        connection_id = next(iter(middleware.message_counts.keys()))
        middleware.message_counts[connection_id]["count"] = middleware.MAX_MESSAGES_PER_MINUTE
        
        # Try to receive more messages (should NOT hit rate limit for staff)
        wrapped_receive = scope["_rate_limited_receive"]
        message = await wrapped_receive()
        
        # Should NOT get a close message, but a regular message
        self.assertEqual(message["type"], "websocket.receive")

    async def test_cleanup_on_disconnect(self):
        """Test that connection counters are cleaned up on disconnect"""
        inner_mock = MockInner(connected=True)
        middleware = RateLimitMiddleware(inner_mock)
        
        # Create scope with user
        scope = {
            "type": "websocket.connect",
            "user": self.user
        }
        
        # Start with a connection count
        user_id = str(self.user.id)
        middleware.connections[user_id] = 1
        
        # Setup receive/send functions
        async def mock_receive():
            return {"type": "websocket.connect"}
        
        async def mock_send(message):
            return None
        
        # Connect
        await middleware(scope, mock_receive, mock_send)
        
        # Should now have 2 connections
        self.assertEqual(middleware.connections[user_id], 2)
        
        # Get connection ID and ensure it's in message_counts
        connection_id = next(iter(middleware.message_counts.keys()))
        self.assertIn(connection_id, middleware.message_counts)
        
        # Call disconnect handler
        await scope["websocket_disconnect"]({"type": "websocket.disconnect", "code": 1000})
        
        # Connection count should be decremented
        self.assertEqual(middleware.connections[user_id], 1)
        
        # Message count for this connection should be removed
        self.assertNotIn(connection_id, middleware.message_counts)


class CSRFProtectionMiddlewareTests(TestCase):
    async def setUp(self):
        pass

    async def test_valid_origin(self):
        """Test that requests with valid origins are allowed"""
        inner_mock = MockInner(connected=True)
        with patch('django.conf.settings') as mock_settings:
            mock_settings.CSRF_TRUSTED_ORIGINS = ['https://example.com']
            
            middleware = CSRFProtectionMiddleware(inner_mock)
            
            # Create scope with valid origin
            scope = {
                "type": "websocket",
                "headers": [(b"origin", b"https://example.com")]
            }
            
            # Should pass through to inner application
            await middleware(scope, AsyncMock(), AsyncMock())
            self.assertTrue(inner_mock.called)

    async def test_invalid_origin(self):
        """Test that requests with invalid origins are rejected"""
        inner_mock = MockInner(connected=True)
        with patch('django.conf.settings') as mock_settings:
            mock_settings.CSRF_TRUSTED_ORIGINS = ['https://example.com']
            
            middleware = CSRFProtectionMiddleware(inner_mock)
            
            # Create scope with invalid origin
            scope = {
                "type": "websocket",
                "headers": [(b"origin", b"https://malicious-site.com")]
            }
            
            # Should be rejected
            result = await middleware(scope, AsyncMock(), AsyncMock())
            self.assertIsNone(result)
            self.assertFalse(inner_mock.called)

    async def test_missing_origin(self):
        """Test that requests with missing origins are rejected"""
        inner_mock = MockInner(connected=True)
        middleware = CSRFProtectionMiddleware(inner_mock)
        
        # Create scope with no origin header
        scope = {
            "type": "websocket",
            "headers": []
        }
        
        # Should be rejected
        result = await middleware(scope, AsyncMock(), AsyncMock())
        self.assertIsNone(result)
        self.assertFalse(inner_mock.called)

    async def test_fallback_to_cors_settings(self):
        """Test fallback to CORS_ALLOWED_ORIGINS if CSRF_TRUSTED_ORIGINS is not set"""
        inner_mock = MockInner(connected=True)
        with patch('django.conf.settings') as mock_settings:
            mock_settings.CSRF_TRUSTED_ORIGINS = []
            mock_settings.CORS_ALLOWED_ORIGINS = ['https://example.com']
            
            middleware = CSRFProtectionMiddleware(inner_mock)
            
            # Create scope with valid origin from CORS settings
            scope = {
                "type": "websocket",
                "headers": [(b"origin", b"https://example.com")]
            }
            
            # Should pass through to inner application
            await middleware(scope, AsyncMock(), AsyncMock())
            self.assertTrue(inner_mock.called)

    async def test_non_websocket_request(self):
        """Test that non-websocket requests pass through"""
        inner_mock = MockInner(connected=True)
        middleware = CSRFProtectionMiddleware(inner_mock)
        
        # Create scope for non-websocket request
        scope = {
            "type": "http",
            "headers": []
        }
        
        # Should pass through to inner application
        await middleware(scope, AsyncMock(), AsyncMock())
        self.assertTrue(inner_mock.called)


class WebSocketSecurityStackTests(TestCase):
    async def setUp(self):
        # Create test user
        self.user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

    async def tearDown(self):
        await database_sync_to_async(User.objects.all().delete)()

    @patch('notifications.consumers.AuthMiddlewareStack')
    @patch('notifications.consumers.RateLimitMiddleware')
    @patch('notifications.consumers.CSRFProtectionMiddleware')
    async def test_middleware_stack_order(self, mock_csrf, mock_rate_limit, mock_auth):
        """Test that middleware stack is constructed in the correct order"""
        inner_app = MockInner(connected=True)
        
        # Setup mocks to pass through to the next middleware
        mock_csrf.return_value = AsyncMock()
        mock_rate_limit.return_value = AsyncMock()
        mock_auth.return_value = AsyncMock()
        
        # Create the stack
        stack = WebSocketSecurityMiddlewareStack(inner_app)
        
        # Check that middlewares were applied in the correct order
        mock_auth.assert_called_once()
        mock_rate_limit.assert_called_once()
        mock_csrf.assert_called_once()
        
        # The order should be: Auth -> RateLimit -> CSRF -> inner
        mock_auth.assert_called_with(mock_rate_limit.return_value)
        mock_rate_limit.assert_called_with(mock_csrf.return_value)
        mock_csrf.assert_called_with(inner_app) 