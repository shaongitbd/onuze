import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from posts.models import Subreddit, SubredditModerator, SubredditRule

User = get_user_model()

class SubredditTests(APITestCase):
    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='Admin@123',
            is_verified=True
        )
        
        self.mod_user = User.objects.create_user(
            username='moderator',
            email='mod@example.com',
            password='Mod@123',
            is_verified=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='Regular@123',
            is_verified=True
        )
        
        # Create a subreddit
        self.subreddit = Subreddit.objects.create(
            name='testsubreddit',
            description='Test subreddit description',
            created_by=self.admin_user
        )
        
        # Add moderator
        SubredditModerator.objects.create(
            subreddit=self.subreddit,
            user=self.mod_user
        )
        
        # Add subreddit rule
        self.rule = SubredditRule.objects.create(
            subreddit=self.subreddit,
            title='Be civil',
            description='No personal attacks or harassment'
        )
        
        # URLs
        self.list_create_url = reverse('subreddit-list')
        self.detail_url = reverse('subreddit-detail', kwargs={'name': self.subreddit.name})
        self.join_url = reverse('subreddit-join', kwargs={'name': self.subreddit.name})
        self.leave_url = reverse('subreddit-leave', kwargs={'name': self.subreddit.name})
        self.mod_url = reverse('subreddit-moderators', kwargs={'name': self.subreddit.name})
        self.rules_url = reverse('subreddit-rules', kwargs={'name': self.subreddit.name})
        
        # Client
        self.client = APIClient()

    def test_list_subreddits(self):
        """Test listing all subreddits"""
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.subreddit.name)

    def test_create_subreddit_authenticated(self):
        """Test creating a subreddit when authenticated"""
        self.client.force_authenticate(user=self.regular_user)
        
        data = {
            'name': 'newsubreddit',
            'description': 'New subreddit description',
            'rules': [
                {'title': 'No spam', 'description': 'No spam or self-promotion'},
                {'title': 'Be nice', 'description': 'Be nice to others'}
            ]
        }
        
        response = self.client.post(
            self.list_create_url, 
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], data['name'])
        self.assertEqual(response.data['description'], data['description'])
        self.assertEqual(response.data['created_by'], self.regular_user.username)
        
        # Verify user was made a moderator
        subreddit = Subreddit.objects.get(name=data['name'])
        is_mod = SubredditModerator.objects.filter(
            subreddit=subreddit, 
            user=self.regular_user
        ).exists()
        self.assertTrue(is_mod)
        
        # Verify rules were created
        rules = SubredditRule.objects.filter(subreddit=subreddit)
        self.assertEqual(rules.count(), len(data['rules']))

    def test_create_subreddit_unauthenticated(self):
        """Test creating a subreddit when not authenticated (should fail)"""
        data = {
            'name': 'newsubreddit',
            'description': 'New subreddit description'
        }
        
        response = self.client.post(
            self.list_create_url, 
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_subreddit_invalid_name(self):
        """Test creating a subreddit with invalid name"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Test with invalid characters
        data = {
            'name': 'invalid subreddit!',
            'description': 'Invalid name with spaces and special chars'
        }
        
        response = self.client.post(
            self.list_create_url, 
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        
        # Test with name that's too long
        data = {
            'name': 'a' * 50,  # Most platforms limit community names
            'description': 'Name too long'
        }
        
        response = self.client.post(
            self.list_create_url, 
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_retrieve_subreddit(self):
        """Test retrieving a single subreddit"""
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.subreddit.name)
        self.assertEqual(response.data['description'], self.subreddit.description)
        self.assertEqual(response.data['created_by'], self.admin_user.username)
        
        # Check if moderators are included
        self.assertIn('moderators', response.data)
        self.assertEqual(len(response.data['moderators']), 2)  # Admin and mod
        
        # Check if rules are included
        self.assertIn('rules', response.data)
        self.assertEqual(len(response.data['rules']), 1)
        self.assertEqual(response.data['rules'][0]['title'], self.rule.title)

    def test_update_subreddit_as_creator(self):
        """Test updating a subreddit as the creator"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'description': 'Updated subreddit description',
        }
        
        response = self.client.patch(
            self.detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], data['description'])
        
        # Refresh from DB to verify
        self.subreddit.refresh_from_db()
        self.assertEqual(self.subreddit.description, data['description'])

    def test_update_subreddit_as_moderator(self):
        """Test updating a subreddit as a moderator"""
        self.client.force_authenticate(user=self.mod_user)
        
        data = {
            'description': 'Moderator updated description',
        }
        
        response = self.client.patch(
            self.detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], data['description'])

    def test_update_subreddit_as_regular_user(self):
        """Test updating a subreddit as a regular user (should fail)"""
        self.client.force_authenticate(user=self.regular_user)
        
        data = {
            'description': 'Unauthorized update attempt',
        }
        
        response = self.client.patch(
            self.detail_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_subreddit_as_creator(self):
        """Test deleting a subreddit as the creator"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Subreddit.objects.filter(name=self.subreddit.name).exists())

    def test_delete_subreddit_as_moderator(self):
        """Test deleting a subreddit as a moderator (should fail)"""
        self.client.force_authenticate(user=self.mod_user)
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Subreddit.objects.filter(name=self.subreddit.name).exists())

    def test_join_subreddit(self):
        """Test joining a subreddit"""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.post(self.join_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.subreddit.members.filter(id=self.regular_user.id).exists())

    def test_leave_subreddit(self):
        """Test leaving a subreddit"""
        # Add user as member first
        self.subreddit.members.add(self.regular_user)
        
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.post(self.leave_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.subreddit.members.filter(id=self.regular_user.id).exists())

    def test_add_moderator(self):
        """Test adding a moderator to a subreddit"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'username': self.regular_user.username,
            'action': 'add'
        }
        
        response = self.client.post(
            self.mod_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(SubredditModerator.objects.filter(
            subreddit=self.subreddit, 
            user=self.regular_user
        ).exists())

    def test_remove_moderator(self):
        """Test removing a moderator from a subreddit"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'username': self.mod_user.username,
            'action': 'remove'
        }
        
        response = self.client.post(
            self.mod_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SubredditModerator.objects.filter(
            subreddit=self.subreddit, 
            user=self.mod_user
        ).exists())

    def test_add_rule(self):
        """Test adding a rule to a subreddit"""
        self.client.force_authenticate(user=self.mod_user)
        
        data = {
            'title': 'No politics',
            'description': 'Political discussions are not allowed'
        }
        
        response = self.client.post(
            self.rules_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SubredditRule.objects.filter(
            subreddit=self.subreddit,
            title=data['title']
        ).exists())

    def test_update_rule(self):
        """Test updating a subreddit rule"""
        self.client.force_authenticate(user=self.mod_user)
        
        rule_url = reverse('subreddit-rule-detail', kwargs={
            'name': self.subreddit.name,
            'rule_id': self.rule.id
        })
        
        data = {
            'description': 'Updated rule description'
        }
        
        response = self.client.patch(
            rule_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], data['description'])
        
        # Refresh from DB
        self.rule.refresh_from_db()
        self.assertEqual(self.rule.description, data['description'])

    def test_delete_rule(self):
        """Test deleting a subreddit rule"""
        self.client.force_authenticate(user=self.admin_user)
        
        rule_url = reverse('subreddit-rule-detail', kwargs={
            'name': self.subreddit.name,
            'rule_id': self.rule.id
        })
        
        response = self.client.delete(rule_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SubredditRule.objects.filter(id=self.rule.id).exists()) 