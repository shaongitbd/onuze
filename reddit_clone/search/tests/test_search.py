import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from posts.models import Post, Subreddit
from comments.models import Comment
from unittest.mock import patch, MagicMock
import time

User = get_user_model()

class SearchTests(APITestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestP@ssw0rd',
            is_verified=True
        )
        
        # Create subreddits with searchable terms
        self.subreddit1 = Subreddit.objects.create(
            name='technology',
            description='All about technology and gadgets',
            created_by=self.user
        )
        
        self.subreddit2 = Subreddit.objects.create(
            name='programming',
            description='Coding discussions and tech news',
            created_by=self.user
        )
        
        # Create posts with searchable terms
        self.post1 = Post.objects.create(
            title='Python Tips for Beginners',
            content='Python is a great programming language for beginners',
            author=self.user,
            subreddit=self.subreddit2
        )
        
        self.post2 = Post.objects.create(
            title='New JavaScript Framework Released',
            content='A new JavaScript framework has been released with amazing features',
            author=self.user,
            subreddit=self.subreddit1
        )
        
        self.post3 = Post.objects.create(
            title='Best Programming Books',
            content='Here are the best books for learning programming languages',
            author=self.user,
            subreddit=self.subreddit2
        )
        
        # Create comments with searchable terms
        self.comment1 = Comment.objects.create(
            post=self.post1,
            author=self.user,
            content='Python is indeed very beginner-friendly compared to other languages'
        )
        
        self.comment2 = Comment.objects.create(
            post=self.post2,
            author=self.user,
            content='Too many JavaScript frameworks these days!'
        )
        
        # URLs
        self.search_url = reverse('search')
        
        # Client
        self.client = APIClient()

    def test_search_posts(self):
        """Test searching for posts"""
        response = self.client.get(f"{self.search_url}?q=python&type=post")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('posts', response.data)
        self.assertEqual(len(response.data['posts']), 2)  # Both post1 and post3 contain "python"
        
        # Verify search results contain correct posts
        post_titles = [post['title'] for post in response.data['posts']]
        self.assertIn(self.post1.title, post_titles)
        
        # Should search in content too
        self.assertIn(self.post3.title, post_titles)
        
        # Should not include unrelated posts
        self.assertNotIn(self.post2.title, post_titles)

    def test_search_comments(self):
        """Test searching for comments"""
        response = self.client.get(f"{self.search_url}?q=beginner&type=comment")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('comments', response.data)
        self.assertEqual(len(response.data['comments']), 1)
        
        # Verify search result contains correct comment
        self.assertEqual(response.data['comments'][0]['id'], str(self.comment1.id))
        self.assertIn('beginner', response.data['comments'][0]['content'])
        
        # Verify post info is included
        self.assertEqual(response.data['comments'][0]['post_title'], self.post1.title)

    def test_search_subreddits(self):
        """Test searching for subreddits"""
        response = self.client.get(f"{self.search_url}?q=tech&type=subreddit")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('subreddits', response.data)
        self.assertEqual(len(response.data['subreddits']), 2)  # Both subreddits contain "tech"
        
        # Verify search results contain correct subreddits
        subreddit_names = [sr['name'] for sr in response.data['subreddits']]
        self.assertIn(self.subreddit1.name, subreddit_names)
        self.assertIn(self.subreddit2.name, subreddit_names)

    def test_search_all(self):
        """Test searching across all content types"""
        response = self.client.get(f"{self.search_url}?q=programming")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return results for all types
        self.assertIn('posts', response.data)
        self.assertIn('comments', response.data)
        self.assertIn('subreddits', response.data)
        
        # Verify posts results
        self.assertGreaterEqual(len(response.data['posts']), 2)  # At least post1 and post3
        
        # Verify subreddit results
        self.assertGreaterEqual(len(response.data['subreddits']), 1)  # At least subreddit2
        
        # Verify subreddit results contain correct subreddits
        subreddit_names = [sr['name'] for sr in response.data['subreddits']]
        self.assertIn(self.subreddit2.name, subreddit_names)

    def test_search_with_pagination(self):
        """Test search results with pagination"""
        # Create more posts for pagination testing
        for i in range(15):
            Post.objects.create(
                title=f'Programming post {i}',
                content=f'Programming content {i}',
                author=self.user,
                subreddit=self.subreddit2
            )
        
        # Test first page (default limit is 10)
        response = self.client.get(f"{self.search_url}?q=programming&type=post")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('posts', response.data)
        self.assertEqual(len(response.data['posts']), 10)  # Default page size
        self.assertIn('next', response.data)  # Should have next page
        self.assertNotIn('previous', response.data)  # No previous page for first page
        
        # Get next page
        next_page_url = response.data['next'].split('?')[1]  # Extract query params
        response = self.client.get(f"{self.search_url}?{next_page_url}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('posts', response.data)
        self.assertGreaterEqual(len(response.data['posts']), 1)  # At least one result on second page
        self.assertIn('previous', response.data)  # Should have previous page

    def test_search_with_custom_page_size(self):
        """Test search with custom page size"""
        response = self.client.get(f"{self.search_url}?q=programming&type=post&limit=2")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('posts', response.data)
        self.assertEqual(len(response.data['posts']), 2)  # Custom page size

    def test_search_no_results(self):
        """Test search with no matching results"""
        response = self.client.get(f"{self.search_url}?q=nonexistentterm")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('posts', response.data)
        self.assertIn('comments', response.data)
        self.assertIn('subreddits', response.data)
        
        # All result lists should be empty
        self.assertEqual(len(response.data['posts']), 0)
        self.assertEqual(len(response.data['comments']), 0)
        self.assertEqual(len(response.data['subreddits']), 0)

    def test_search_with_filters(self):
        """Test search with additional filters"""
        # Filter by subreddit
        response = self.client.get(
            f"{self.search_url}?q=programming&type=post&subreddit={self.subreddit1.name}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('posts', response.data)
        
        # Should only return posts from the specified subreddit
        for post in response.data['posts']:
            self.assertEqual(post['subreddit'], self.subreddit1.name)
        
        # Filter by author
        response = self.client.get(
            f"{self.search_url}?q=programming&type=post&author={self.user.username}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only return posts from the specified author
        for post in response.data['posts']:
            self.assertEqual(post['author'], self.user.username)

    def test_search_with_sorting(self):
        """Test search results with different sorting options"""
        # Sort by newest (default)
        response = self.client.get(f"{self.search_url}?q=programming&type=post&sort=newest")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # First result should be the most recent post
        first_created_at = response.data['posts'][0]['created_at']
        for post in response.data['posts'][1:]:
            self.assertGreaterEqual(first_created_at, post['created_at'])
        
        # Sort by relevance
        response = self.client.get(f"{self.search_url}?q=python&type=post&sort=relevance")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Posts with "python" in title should be ranked higher than those with it only in content
        post_ids = [post['id'] for post in response.data['posts']]
        if len(post_ids) >= 2:
            # post1 has "Python" in title, should come before post3 which has it only in content
            self.assertLess(post_ids.index(str(self.post1.id)), post_ids.index(str(self.post3.id)))

    def test_malformed_search_query(self):
        """Test search with malformed query parameters"""
        # Empty query
        response = self.client.get(f"{self.search_url}?q=")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid content type
        response = self.client.get(f"{self.search_url}?q=test&type=invalid")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid sort option
        response = self.client.get(f"{self.search_url}?q=test&sort=invalid")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('search.views.SearchPagination.get_paginated_response')
    def test_search_highlight(self, mock_paginate):
        """Test that search results highlight matching terms"""
        # Mock the pagination to examine the raw search results
        mock_paginate.side_effect = lambda results: results
        
        response = self.client.get(f"{self.search_url}?q=python&type=post&highlight=true")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check for highlighting in title or content
        for post in response.data:
            title_or_content_has_highlight = False
            if '<em>Python</em>' in post['title'] or '<em>python</em>' in post['content']:
                title_or_content_has_highlight = True
            
            self.assertTrue(title_or_content_has_highlight, 
                           f"Post {post['id']} should have highlighted search term")

    def test_search_performance(self):
        """Test search performance under load"""
        # Create a large number of posts to search through
        for i in range(100): # Reduced for faster testing
            post = Post.objects.create(
                title=f'Performance test post {i}',
                content=f'Testing search performance with post {i}',
                author=self.user,
                subreddit=self.subreddit1
            )
            # Add a comment to each post
            Comment.objects.create(
                post=post,
                author=self.user,
                content=f'Performance test comment {i}'
            )
        
        # Search a term that will match all the new posts
        start_time = time.time()
        
        response = self.client.get(f"{self.search_url}?q=performance&type=post")
        
        end_time = time.time()
        search_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Search should return results in a reasonable time (less than 1 second)
        self.assertLess(search_time, 1.0, 
                      f"Search took too long: {search_time} seconds")
        
        # Verify we got some results
        self.assertGreater(len(response.data['posts']), 0) 