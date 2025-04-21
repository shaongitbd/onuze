import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

User = get_user_model()

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-register')
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongP@ssw0rd',
            'password2': 'StrongP@ssw0rd'
        }
        self.login_data = {
            'username': 'testuser',
            'password': 'StrongP@ssw0rd'
        }

    def test_user_registration_success(self):
        """Test successful user registration"""
        # Mock the email sending functionality
        with patch('users.views.send_verification_email'):
            response = self.client.post(
                self.register_url,
                data=json.dumps(self.user_data),
                content_type='application/json'
            )
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('email_verification_sent', response.data)
        self.assertTrue(response.data['email_verification_sent'])
        
        # Check that user exists but is not verified
        user = User.objects.get(username=self.user_data['username'])
        self.assertFalse(user.is_verified)

    def test_user_registration_weak_password(self):
        """Test registration with weak password is rejected"""
        weak_password_data = self.user_data.copy()
        weak_password_data['password'] = 'password123'
        weak_password_data['password2'] = 'password123'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(weak_password_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_registration_password_mismatch(self):
        """Test registration with mismatching passwords is rejected"""
        mismatch_data = self.user_data.copy()
        mismatch_data['password2'] = 'DifferentP@ssw0rd'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(mismatch_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_user_registration_duplicate_username(self):
        """Test registration with existing username is rejected"""
        # Create a user first
        with patch('users.views.send_verification_email'):
            self.client.post(
                self.register_url,
                data=json.dumps(self.user_data),
                content_type='application/json'
            )
        
        # Try to register with the same username
        duplicate_data = self.user_data.copy()
        duplicate_data['email'] = 'another@example.com'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(duplicate_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_user_login_success(self):
        """Test successful user login with verified account"""
        # Register and verify a user
        with patch('users.views.send_verification_email'):
            self.client.post(
                self.register_url,
                data=json.dumps(self.user_data),
                content_type='application/json'
            )
        
        # Manually verify the user
        user = User.objects.get(username=self.user_data['username'])
        user.is_verified = True
        user.save()
        
        # Login
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_unverified(self):
        """Test login with unverified account is rejected"""
        # Register user but don't verify
        with patch('users.views.send_verification_email'):
            self.client.post(
                self.register_url,
                data=json.dumps(self.user_data),
                content_type='application/json'
            )
        
        # Try to login
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.login_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertIn('verify', response.data['detail'].lower())

    def test_user_login_wrong_credentials(self):
        """Test login with incorrect credentials is rejected"""
        # Register and verify a user
        with patch('users.views.send_verification_email'):
            self.client.post(
                self.register_url,
                data=json.dumps(self.user_data),
                content_type='application/json'
            )
        
        user = User.objects.get(username=self.user_data['username'])
        user.is_verified = True
        user.save()
        
        # Try to login with wrong password
        wrong_data = self.login_data.copy()
        wrong_data['password'] = 'WrongP@ssw0rd'
        
        response = self.client.post(
            self.login_url,
            data=json.dumps(wrong_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Test refreshing the JWT token"""
        # Register and verify a user
        with patch('users.views.send_verification_email'):
            self.client.post(
                self.register_url,
                data=json.dumps(self.user_data),
                content_type='application/json'
            )
        
        user = User.objects.get(username=self.user_data['username'])
        user.is_verified = True
        user.save()
        
        # Login to get tokens
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.login_data),
            content_type='application/json'
        )
        
        refresh_token = response.data['refresh']
        
        # Refresh the token
        response = self.client.post(
            self.refresh_url,
            data=json.dumps({'refresh': refresh_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    @patch('users.views.send_password_reset_email')
    def test_password_reset_request(self, mock_send_email):
        """Test requesting a password reset"""
        # Register and verify a user
        with patch('users.views.send_verification_email'):
            self.client.post(
                self.register_url,
                data=json.dumps(self.user_data),
                content_type='application/json'
            )
        
        user = User.objects.get(username=self.user_data['username'])
        user.is_verified = True
        user.save()
        
        # Request password reset
        reset_url = reverse('password-reset-request')
        response = self.client.post(
            reset_url,
            data=json.dumps({'email': self.user_data['email']}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_send_email.called)

    def test_email_verification(self):
        """Test email verification"""
        # Register a user
        with patch('users.views.send_verification_email') as mock_send_email:
            self.client.post(
                self.register_url,
                data=json.dumps(self.user_data),
                content_type='application/json'
            )
            
            # Ensure email was attempted to be sent
            self.assertTrue(mock_send_email.called)
        
        # Get the user and their token
        user = User.objects.get(username=self.user_data['username'])
        self.assertFalse(user.is_verified)
        
        # Mock getting the token
        with patch('users.models.VerificationToken.objects.get') as mock_get_token:
            token_instance = type('VerificationToken', (), {'user': user, 'token': 'test-token'})
            mock_get_token.return_value = token_instance
            
            # Verify email
            verify_url = reverse('verify-email', kwargs={'token': 'test-token'})
            response = self.client.get(verify_url)
            
            # Should redirect to frontend on success
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        
        # Refresh user and check verified status
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_logout(self):
        """Test user logout by blacklisting the refresh token"""
        # Register and verify a user
        with patch('users.views.send_verification_email'):
            self.client.post(
                self.register_url,
                data=json.dumps(self.user_data),
                content_type='application/json'
            )
        
        user = User.objects.get(username=self.user_data['username'])
        user.is_verified = True
        user.save()
        
        # Login to get tokens
        response = self.client.post(
            self.login_url,
            data=json.dumps(self.login_data),
            content_type='application/json'
        )
        
        refresh_token = response.data['refresh']
        
        # Logout
        logout_url = reverse('logout')
        response = self.client.post(
            logout_url,
            data=json.dumps({'refresh': refresh_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        
        # Try to refresh the token (should fail)
        response = self.client.post(
            self.refresh_url,
            data=json.dumps({'refresh': refresh_token}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 