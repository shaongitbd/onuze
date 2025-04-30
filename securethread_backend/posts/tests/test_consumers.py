import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from django.urls import path

from posts.models import Post, Subreddit
from posts.consumers import PostConsumer

User = get_user_model()

class PostConsumerTests(TestCase):
    async def setUp(self):
        # Create a test user
        self.user = await database_sync_to_async(User.objects.create_user)(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        # Create a test subreddit
        self.subreddit = await database_sync_to_async(Subreddit.objects.create)(
            name='testsubreddit',
            description='Test subreddit description',
            created_by=self.user
        )

        # Create a test post
        self.post = await database_sync_to_async(Post.objects.create)(
            title='Test Post',
            content='Test content',
            author=self.user,
            subreddit=self.subreddit
        )

        # Define application routing for tests
        self.application = URLRouter([
            path('ws/post/<str:post_id>/', PostConsumer.as_asgi())
        ])

    async def tearDown(self):
        await database_sync_to_async(Post.objects.all().delete)()
        await database_sync_to_async(Subreddit.objects.all().delete)()
        await database_sync_to_async(User.objects.all().delete)()

    async def test_connect_to_valid_post(self):
        """Test connecting to a valid post's WebSocket"""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/post/{self.post.id}/'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_connect_to_invalid_post(self):
        """Test connecting to an invalid post's WebSocket"""
        communicator = WebsocketCommunicator(
            self.application,
            '/ws/post/99999/'  # Non-existent post ID
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_post_update_event(self):
        """Test receiving post update event"""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/post/{self.post.id}/'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a post_update event to the consumer
        post_data = {'title': 'Updated Title', 'content': 'Updated content'}
        await communicator.send_json_to({
            'type': 'post_update',
            'post_data': post_data
        })

        # Verify the response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'post_update')
        self.assertEqual(response['post_data'], post_data)

        await communicator.disconnect()

    async def test_new_comment_event(self):
        """Test receiving new comment event"""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/post/{self.post.id}/'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a new_comment event to the consumer
        comment_data = {
            'id': '123',
            'author': 'testuser',
            'content': 'Test comment',
            'created_at': '2023-01-01T12:00:00Z'
        }
        await communicator.send_json_to({
            'type': 'new_comment',
            'comment_data': comment_data
        })

        # Verify the response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'new_comment')
        self.assertEqual(response['comment_data'], comment_data)

        await communicator.disconnect()

    async def test_vote_update_event(self):
        """Test receiving vote update event"""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/post/{self.post.id}/'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a vote_update event to the consumer
        vote_data = {
            'upvotes': 10,
            'downvotes': 5,
            'score': 5
        }
        await communicator.send_json_to({
            'type': 'vote_update',
            'upvotes': vote_data['upvotes'],
            'downvotes': vote_data['downvotes'],
            'score': vote_data['score']
        })

        # Verify the response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'vote_update')
        self.assertEqual(response['upvotes'], vote_data['upvotes'])
        self.assertEqual(response['downvotes'], vote_data['downvotes'])
        self.assertEqual(response['score'], vote_data['score'])

        await communicator.disconnect() 