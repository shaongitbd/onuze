import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from posts.models import Post, Subreddit, PostVote
from unittest.mock import patch, MagicMock

User = get_user_model()

class PostTests(APITestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestP@ssw0rd',
            is_verified=True
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherP@ssw0rd',
            is_verified=True
        )
        
        # Create subreddit
        self.subreddit = Subreddit.objects.create(
            name='testsubreddit',
            description='Test subreddit description',
            created_by=self.user
        )
        
        # Create post
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content',
            author=self.user,
            subreddit=self.subreddit
        )
        
        # URLs
        self.list_create_url = reverse('post-list')
        self.detail_url = reverse('post-detail', kwargs={'pk': self.post.pk})
        self.vote_url = reverse('post-vote', kwargs={'pk': self.post.pk})
        self.subreddit_posts_url = reverse('subreddit-posts', kwargs={'name': self.subreddit.name})
        self.user_posts_url = reverse('user-posts', kwargs={'username': self.user.username})
        
        # Client
        self.client = APIClient()

    def test_list_posts(self):
        """Test listing all posts"""
        response = self.client.get(self.list_create_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post.title)
        self.assertEqual(response.data['results'][0]['author'], self.user.username)

    def test_list_posts_by_subreddit(self):
        """Test listing posts by subreddit"""
        response = self.client.get(self.subreddit_posts_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post.title)
        self.assertEqual(response.data['results'][0]['subreddit'], self.subreddit.name)

    def test_list_posts_by_user(self):
        """Test listing posts by user"""
        response = self.client.get(self.user_posts_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], self.post.title)
        self.assertEqual(response.data['results'][0]['author'], self.user.username)

    def test_create_post_authenticated(self):
        """Test creating a post when authenticated"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'New Test Post',
            'content': 'This is a new test post content',
            'subreddit': self.subreddit.name
        }
        
        response = self.client.post(
            self.list_create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['content'], data['content'])
        self.assertEqual(response.data['subreddit'], data['subreddit'])
        self.assertEqual(response.data['author'], self.user.username)
        
        # Verify post was created in DB
        self.assertTrue(Post.objects.filter(title=data['title']).exists())

    def test_create_post_unauthenticated(self):
        """Test creating a post when not authenticated (should fail)"""
        data = {
            'title': 'New Test Post',
            'content': 'This is a new test post content',
            'subreddit': self.subreddit.name
        }
        
        response = self.client.post(
            self.list_create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post_invalid_data(self):
        """Test creating a post with invalid data"""
        self.client.force_authenticate(user=self.user)
        
        # Test with empty title
        data = {
            'title': '',
            'content': 'This is a new test post content',
            'subreddit': self.subreddit.name
        }
        
        response = self.client.post(
            self.list_create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
        
        # Test with non-existent subreddit
        data = {
            'title': 'New Test Post',
            'content': 'This is a new test post content',
            'subreddit': 'nonexistentsubreddit'
        }
        
        response = self.client.post(
            self.list_create_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('subreddit', response.data)

    def test_retrieve_post(self):
        """Test retrieving a single post"""
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.post.title)
        self.assertEqual(response.data['content'], self.post.content)
        self.assertEqual(response.data['author'], self.user.username)
        self.assertEqual(response.data['subreddit'], self.subreddit.name)
        
        # Check vote counts exist
        self.assertIn('upvotes', response.data)
        self.assertIn('downvotes', response.data)
        self.assertIn('score', response.data)

    def test_update_post_as_author(self):
        """Test updating a post as the author"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'Updated Post Title',
            'content': 'This is updated content'
        }
        
        response = self.client.patch(
            self.detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['content'], data['content'])
        
        # Refresh from DB
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, data['title'])
        self.assertEqual(self.post.content, data['content'])
        self.assertTrue(self.post.is_edited)

    def test_update_post_as_non_author(self):
        """Test updating a post as a non-author (should fail)"""
        self.client.force_authenticate(user=self.other_user)
        
        data = {
            'title': 'Unauthorized Update',
            'content': 'This should fail'
        }
        
        response = self.client.patch(
            self.detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify post wasn't updated
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.title, data['title'])

    def test_update_post_subreddit(self):
        """Test that changing the subreddit of a post is not allowed"""
        self.client.force_authenticate(user=self.user)
        
        # Create a new subreddit
        new_subreddit = Subreddit.objects.create(
            name='newsubreddit',
            description='New subreddit description',
            created_by=self.user
        )
        
        data = {
            'subreddit': new_subreddit.name
        }
        
        response = self.client.patch(
            self.detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should not allow changing subreddit
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('subreddit', response.data)
        
        # Verify subreddit wasn't changed
        self.post.refresh_from_db()
        self.assertEqual(self.post.subreddit.name, self.subreddit.name)

    def test_delete_post_as_author(self):
        """Test deleting a post as the author"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_delete_post_as_non_author(self):
        """Test deleting a post as a non-author (should fail)"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_upvote_post(self):
        """Test upvoting a post"""
        self.client.force_authenticate(user=self.other_user)
        
        data = {'vote_type': 'upvote'}
        
        response = self.client.post(
            self.vote_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['upvotes'], 1)
        self.assertEqual(response.data['downvotes'], 0)
        self.assertEqual(response.data['score'], 1)
        
        # Verify vote was created
        self.assertTrue(PostVote.objects.filter(
            post=self.post,
            user=self.other_user,
            vote_type='upvote'
        ).exists())

    def test_downvote_post(self):
        """Test downvoting a post"""
        self.client.force_authenticate(user=self.other_user)
        
        data = {'vote_type': 'downvote'}
        
        response = self.client.post(
            self.vote_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['upvotes'], 0)
        self.assertEqual(response.data['downvotes'], 1)
        self.assertEqual(response.data['score'], -1)
        
        # Verify vote was created
        self.assertTrue(PostVote.objects.filter(
            post=self.post,
            user=self.other_user,
            vote_type='downvote'
        ).exists())

    def test_change_vote(self):
        """Test changing a vote from upvote to downvote"""
        self.client.force_authenticate(user=self.other_user)
        
        # First upvote
        PostVote.objects.create(
            post=self.post,
            user=self.other_user,
            vote_type='upvote'
        )
        
        # Then change to downvote
        data = {'vote_type': 'downvote'}
        
        response = self.client.post(
            self.vote_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['upvotes'], 0)
        self.assertEqual(response.data['downvotes'], 1)
        self.assertEqual(response.data['score'], -1)
        
        # Verify vote was changed
        vote = PostVote.objects.get(post=self.post, user=self.other_user)
        self.assertEqual(vote.vote_type, 'downvote')

    def test_remove_vote(self):
        """Test removing a vote"""
        self.client.force_authenticate(user=self.other_user)
        
        # First add a vote
        PostVote.objects.create(
            post=self.post,
            user=self.other_user,
            vote_type='upvote'
        )
        
        # Then remove it
        data = {'vote_type': 'none'}
        
        response = self.client.post(
            self.vote_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['upvotes'], 0)
        self.assertEqual(response.data['downvotes'], 0)
        self.assertEqual(response.data['score'], 0)
        
        # Verify vote was removed
        self.assertFalse(PostVote.objects.filter(
            post=self.post,
            user=self.other_user
        ).exists())

    @patch('posts.views.notify_post_update')
    def test_websocket_notification_on_update(self, mock_notify):
        """Test that WebSocket notifications are sent when a post is updated"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'Updated Post Title',
            'content': 'This content should trigger a WebSocket notification'
        }
        
        response = self.client.patch(
            self.detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_notify.assert_called_once()
        
        # Verify the correct post data was passed to the notification
        args, kwargs = mock_notify.call_args
        self.assertEqual(args[0].id, self.post.id)
        
    @patch('posts.views.notify_vote_update')
    def test_websocket_notification_on_vote(self, mock_notify):
        """Test that WebSocket notifications are sent when a post is voted on"""
        self.client.force_authenticate(user=self.other_user)
        
        data = {'vote_type': 'upvote'}
        
        response = self.client.post(
            self.vote_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_notify.assert_called_once()
        
        # Verify the correct vote data was passed to the notification
        args, kwargs = mock_notify.call_args
        self.assertEqual(args[0].id, self.post.id) 