import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from posts.models import Post, Subreddit
from comments.models import Comment, CommentVote
from unittest.mock import patch, MagicMock
import bleach

User = get_user_model()

class CommentTests(APITestCase):
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
        
        # Create a root comment
        self.root_comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='This is a root comment'
        )
        
        # Create a child comment (reply)
        self.child_comment = Comment.objects.create(
            post=self.post,
            author=self.other_user,
            parent=self.root_comment,
            content='This is a reply to the root comment'
        )
        
        # URLs
        self.post_comments_url = reverse('post-comments', kwargs={'post_id': self.post.id})
        self.comment_detail_url = reverse('comment-detail', kwargs={'pk': self.root_comment.id})
        self.reply_url = reverse('comment-reply', kwargs={'pk': self.root_comment.id})
        self.vote_url = reverse('comment-vote', kwargs={'pk': self.root_comment.id})
        self.child_comment_url = reverse('comment-detail', kwargs={'pk': self.child_comment.id})
        self.child_vote_url = reverse('comment-vote', kwargs={'pk': self.child_comment.id})
        
        # Client
        self.client = APIClient()

    def test_list_post_comments(self):
        """Test listing all comments for a post"""
        response = self.client.get(self.post_comments_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only root comments are returned in the first level
        self.assertEqual(response.data[0]['content'], self.root_comment.content)
        self.assertEqual(response.data[0]['author'], self.user.username)
        
        # Check if child comments are included
        self.assertIn('replies', response.data[0])
        self.assertEqual(len(response.data[0]['replies']), 1)
        self.assertEqual(response.data[0]['replies'][0]['content'], self.child_comment.content)

    def test_create_comment_authenticated(self):
        """Test creating a comment when authenticated"""
        self.client.force_authenticate(user=self.other_user)
        
        data = {
            'content': 'This is a new comment'
        }
        
        response = self.client.post(
            self.post_comments_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], data['content'])
        self.assertEqual(response.data['author'], self.other_user.username)
        self.assertEqual(response.data['post'], self.post.id)
        self.assertIsNone(response.data['parent'])
        
        # Verify comment was created in DB
        self.assertTrue(Comment.objects.filter(content=data['content']).exists())

    def test_create_comment_unauthenticated(self):
        """Test creating a comment when not authenticated (should fail)"""
        data = {
            'content': 'This is a new comment'
        }
        
        response = self.client.post(
            self.post_comments_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_reply_to_comment(self):
        """Test replying to an existing comment"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'content': 'This is a reply to the comment'
        }
        
        response = self.client.post(
            self.reply_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], data['content'])
        self.assertEqual(response.data['author'], self.user.username)
        self.assertEqual(response.data['parent'], self.root_comment.id)
        
        # Verify reply was created in DB
        self.assertTrue(Comment.objects.filter(
            content=data['content'],
            parent=self.root_comment
        ).exists())

    def test_update_comment_as_author(self):
        """Test updating a comment as the author"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'content': 'This is an updated comment'
        }
        
        response = self.client.patch(
            self.comment_detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], data['content'])
        
        # Verify comment was updated in DB
        self.root_comment.refresh_from_db()
        self.assertEqual(self.root_comment.content, data['content'])
        self.assertTrue(self.root_comment.is_edited)

    def test_update_comment_as_non_author(self):
        """Test updating a comment as a non-author (should fail)"""
        self.client.force_authenticate(user=self.other_user)
        
        data = {
            'content': 'This update should fail'
        }
        
        response = self.client.patch(
            self.comment_detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify comment wasn't updated
        self.root_comment.refresh_from_db()
        self.assertNotEqual(self.root_comment.content, data['content'])

    def test_delete_comment_as_author(self):
        """Test deleting a comment as the author"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(self.comment_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify the comment is soft deleted (content replaced, but still exists)
        self.root_comment.refresh_from_db()
        self.assertTrue(self.root_comment.is_deleted)
        self.assertNotEqual(self.root_comment.content, 'This is a root comment')
        self.assertEqual(self.root_comment.content, '[deleted]')

    def test_delete_comment_with_replies(self):
        """Test deleting a comment that has replies (should soft delete)"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(self.comment_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify the comment is soft deleted
        self.root_comment.refresh_from_db()
        self.assertTrue(self.root_comment.is_deleted)
        
        # Verify child comment still exists
        self.child_comment.refresh_from_db()
        self.assertFalse(self.child_comment.is_deleted)
        self.assertEqual(self.child_comment.content, 'This is a reply to the root comment')

    def test_delete_comment_as_non_author(self):
        """Test deleting a comment as a non-author (should fail)"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.delete(self.comment_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify comment wasn't deleted
        self.root_comment.refresh_from_db()
        self.assertFalse(self.root_comment.is_deleted)

    def test_upvote_comment(self):
        """Test upvoting a comment"""
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
        self.assertTrue(CommentVote.objects.filter(
            comment=self.root_comment,
            user=self.other_user,
            vote_type='upvote'
        ).exists())

    def test_downvote_comment(self):
        """Test downvoting a comment"""
        self.client.force_authenticate(user=self.user)
        
        data = {'vote_type': 'downvote'}
        
        response = self.client.post(
            self.child_vote_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['upvotes'], 0)
        self.assertEqual(response.data['downvotes'], 1)
        self.assertEqual(response.data['score'], -1)
        
        # Verify vote was created
        self.assertTrue(CommentVote.objects.filter(
            comment=self.child_comment,
            user=self.user,
            vote_type='downvote'
        ).exists())

    def test_change_vote(self):
        """Test changing a vote from upvote to downvote"""
        self.client.force_authenticate(user=self.other_user)
        
        # First upvote
        CommentVote.objects.create(
            comment=self.root_comment,
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
        vote = CommentVote.objects.get(comment=self.root_comment, user=self.other_user)
        self.assertEqual(vote.vote_type, 'downvote')

    def test_remove_vote(self):
        """Test removing a vote"""
        self.client.force_authenticate(user=self.other_user)
        
        # First add a vote
        CommentVote.objects.create(
            comment=self.root_comment,
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
        self.assertFalse(CommentVote.objects.filter(
            comment=self.root_comment,
            user=self.other_user
        ).exists())

    @patch('comments.views.notify_new_comment')
    def test_websocket_notification_on_new_comment(self, mock_notify):
        """Test that WebSocket notifications are sent when a new comment is created"""
        self.client.force_authenticate(user=self.other_user)
        
        data = {
            'content': 'This comment should trigger a WebSocket notification'
        }
        
        response = self.client.post(
            self.post_comments_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_notify.assert_called_once()
        
        # Verify the correct comment and post data was passed to the notification
        args, kwargs = mock_notify.call_args
        self.assertEqual(args[0].post.id, self.post.id)

    @patch('comments.views.notify_comment_update')
    def test_websocket_notification_on_comment_update(self, mock_notify):
        """Test that WebSocket notifications are sent when a comment is updated"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'content': 'This update should trigger a WebSocket notification'
        }
        
        response = self.client.patch(
            self.comment_detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_notify.assert_called_once()
        
        # Verify the correct comment data was passed to the notification
        args, kwargs = mock_notify.call_args
        self.assertEqual(args[0].id, self.root_comment.id)

    @patch('comments.views.notify_comment_delete')
    def test_websocket_notification_on_comment_delete(self, mock_notify):
        """Test that WebSocket notifications are sent when a comment is deleted"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(self.comment_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_notify.assert_called_once()
        
        # Verify the correct comment and post data was passed to the notification
        args, kwargs = mock_notify.call_args
        self.assertEqual(args[0], self.root_comment.id)
        self.assertEqual(args[1], self.post.id)

    def test_html_sanitization(self):
        """Test that HTML content in comments is properly sanitized"""
        self.client.force_authenticate(user=self.user)
        
        # Try to include potentially dangerous HTML
        dangerous_content = '<script>alert("XSS");</script><p>Valid content</p><iframe src="malicious-site"></iframe>'
        
        data = {
            'content': dangerous_content
        }
        
        response = self.client.post(
            self.post_comments_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify that dangerous tags were removed but safe ones remain
        sanitized_content = bleach.clean(
            dangerous_content,
            tags=['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote'],
            attributes={'a': ['href', 'title']},
            strip=True
        )
        
        self.assertEqual(response.data['content'], sanitized_content)
        self.assertEqual(response.data['content'], 'Valid content')  # Only the <p> tag content should remain 