import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from django.urls import path

from posts.models import Post, Subreddit
from comments.models import Comment
from comments.consumers import CommentConsumer

User = get_user_model()

class CommentConsumerTests(TestCase):
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
            path('ws/comments/<str:post_id>/', CommentConsumer.as_asgi())
        ])

    async def tearDown(self):
        await database_sync_to_async(Comment.objects.all().delete)()
        await database_sync_to_async(Post.objects.all().delete)()
        await database_sync_to_async(Subreddit.objects.all().delete)()
        await database_sync_to_async(User.objects.all().delete)()

    async def test_connect_to_valid_post(self):
        """Test connecting to a valid post's comment WebSocket"""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/comments/{self.post.id}/'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_connect_to_invalid_post(self):
        """Test connecting to an invalid post's comment WebSocket"""
        communicator = WebsocketCommunicator(
            self.application,
            '/ws/comments/99999/'  # Non-existent post ID
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_new_comment_event(self):
        """Test receiving new comment event"""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/comments/{self.post.id}/'
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

    async def test_comment_update_event(self):
        """Test receiving comment update event"""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/comments/{self.post.id}/'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a comment_update event to the consumer
        update_data = {
            'comment_id': '123',
            'content': 'Updated comment content',
            'is_edited': True
        }
        await communicator.send_json_to({
            'type': 'comment_update',
            'comment_id': update_data['comment_id'],
            'content': update_data['content'],
            'is_edited': update_data['is_edited']
        })

        # Verify the response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'comment_update')
        self.assertEqual(response['comment_id'], update_data['comment_id'])
        self.assertEqual(response['content'], update_data['content'])
        self.assertEqual(response['is_edited'], update_data['is_edited'])

        await communicator.disconnect()

    async def test_comment_delete_event(self):
        """Test receiving comment deletion event"""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/comments/{self.post.id}/'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a comment_delete event to the consumer
        comment_id = '123'
        await communicator.send_json_to({
            'type': 'comment_delete',
            'comment_id': comment_id
        })

        # Verify the response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'comment_delete')
        self.assertEqual(response['comment_id'], comment_id)

        await communicator.disconnect()

    async def test_vote_update_event(self):
        """Test receiving vote update event for a comment"""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/comments/{self.post.id}/'
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a vote_update event to the consumer
        vote_data = {
            'comment_id': '123',
            'upvotes': 10,
            'downvotes': 5,
            'score': 5
        }
        await communicator.send_json_to({
            'type': 'vote_update',
            'comment_id': vote_data['comment_id'],
            'upvotes': vote_data['upvotes'],
            'downvotes': vote_data['downvotes'],
            'score': vote_data['score']
        })

        # Verify the response
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'vote_update')
        self.assertEqual(response['comment_id'], vote_data['comment_id'])
        self.assertEqual(response['upvotes'], vote_data['upvotes'])
        self.assertEqual(response['downvotes'], vote_data['downvotes'])
        self.assertEqual(response['score'], vote_data['score'])

        await communicator.disconnect() 