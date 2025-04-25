from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model, login
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
import uuid
import os
import time
import requests
import logging
import jwt
from datetime import timedelta
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail
from communities.models import Community, CommunityMember
from security.models import RefreshToken, AuditLog
from notifications.models import Notification
from .models import Role, UserBlock
from .serializers import (
    UserSerializer, 
    UserBriefSerializer, 
    UserCreateSerializer, 
    UserUpdateSerializer,
    PasswordChangeSerializer, 
    RoleSerializer,
    UserBlockSerializer
)
import pyotp
import qrcode
import io
import base64
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from posts.models import Post
from comments.models import Comment
from communities.models import CommunityMember

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users.
    Uses username for detail view lookups.
    """
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    lookup_field = 'username'  # Use username for lookup
    lookup_url_kwarg = 'username' # Explicitly set URL kwarg (optional but good practice)
    # Default permission is IsAuthenticated, overridden below
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
             # Use brief serializer for lists
            return UserBriefSerializer
        # For retrieve, use the default UserSerializer
        return self.serializer_class
    
    def get_permissions(self):
        if self.action == 'create':
            # Anyone can create a user
            return [permissions.AllowAny()]
        elif self.action in ['retrieve', 'list']:
            # Allow public read for individual profiles, but keep list protected
            # For retrieve (detail view), allow public read
            # For list view, require authentication
            if self.action == 'retrieve':
                 return [permissions.IsAuthenticatedOrReadOnly()]
            else: # list action
                 return [permissions.IsAuthenticated()]
        # Default to IsAuthenticated for other actions (update, destroy, custom actions)
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                
                # Log user creation
                AuditLog.log(
                    action='user_create',
                    entity_type='user',
                    entity_id=user.id,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    status='success'
                )
                
                # Create refresh + access token
                refresh = RefreshToken.for_user(user)
                
                # Send welcome notification if needed
                try:
                    Notification.send_welcome_notification(user)
                except Exception:
                    pass
                
                # Auto-verify user in development
                if settings.DEBUG:
                    user.is_verified = True
                    user.save(update_fields=['is_verified'])
                
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Log failed user creation
                AuditLog.log(
                    action='user_create_failed',
                    entity_type='user',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    status='failed',
                    details={'error': str(e)}
                )
                raise
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_update(self, serializer):
        try:
            instance = serializer.save()
            
            # Log user update
            AuditLog.log(
                action='user_update',
                entity_type='user',
                entity_id=instance.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success'
            )
            
            # Ensure that if two_factor_enabled was turned on or off,
            # we update the secret or clear it
            two_factor_enabled = serializer.validated_data.get('two_factor_enabled', None)
            if two_factor_enabled is not None:
                if two_factor_enabled and not instance.two_factor_secret:
                    # Generate and save a new TOTP secret
                    instance.two_factor_secret = pyotp.random_base32()
                    instance.save(update_fields=['two_factor_secret'])
                elif not two_factor_enabled and instance.two_factor_secret:
                    # Clear the TOTP secret when disabling 2FA
                    instance.two_factor_secret = None
                    instance.save(update_fields=['two_factor_secret'])
        except Exception as e:
            # Log failed user update
            AuditLog.log(
                action='user_update_failed',
                entity_type='user',
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={'error': str(e)}
            )
            raise
    
    def destroy(self, request, *args, **kwargs):
        # We don't actually delete users, just deactivate them
        user = self.get_object()
        
        # Only admins can deactivate other users
        if user != request.user and not request.user.is_staff:
            raise PermissionDenied("You do not have permission to deactivate this user.")
        
        try:
            user.is_active = False
            user.save(update_fields=['is_active'])
            
            # Log user deactivation
            AuditLog.log(
                action='user_deactivate',
                entity_type='user',
                entity_id=user.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status='success'
            )
            
            # Invalidate all user's refresh tokens if user is deactivating self
            if user == request.user:
                try:
                    RefreshToken.revoke_all_for_user(user)
                except Exception:
                    pass
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Log failed user deactivation
            AuditLog.log(
                action='user_deactivate_failed',
                entity_type='user',
                entity_id=user.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={'error': str(e)}
            )
            raise
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        user = self.get_object()
        
        # Import serializer here to avoid circular dependency
        from posts.serializers import PostSerializer
        
        # Pagination parameters
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        # Get user's posts
        posts = Post.objects.filter(user=user, is_deleted=False).order_by('-created_at')[offset:offset+limit]
        
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        user = self.get_object()
        
        # Import serializer here to avoid circular dependency
        from comments.serializers import CommentSerializer
        
        # Pagination parameters
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        # Get user's comments
        comments = Comment.objects.filter(user=user, is_deleted=False).order_by('-created_at')[offset:offset+limit]
        
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def communities(self, request, pk=None):
        user = self.get_object()
        
        # Pagination parameters
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        # Get communities the user is a member of
        communities = user.communities.filter(is_banned=False).order_by('community__name')[offset:offset+limit]
        
        # Get the actual community objects
        community_objects = [membership.community for membership in communities]
        
        serializer = CommunitySerializer(community_objects, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def enable_2fa(self, request):
        """
        Enable 2FA for the current user.
        Generates a TOTP secret and returns a QR code.
        """
        user = request.user
        
        # Generate a new TOTP secret if one doesn't exist
        if not user.two_factor_secret:
            user.two_factor_secret = pyotp.random_base32()
            user.save(update_fields=['two_factor_secret'])
        
        # Create a TOTP provider
        totp = pyotp.TOTP(user.two_factor_secret)
        
        # Generate a QR code URI
        uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Reddit Clone"
        )
        
        # Generate a QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert the image to base64 for easy display in frontend
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Log 2FA setup initiation
        AuditLog.log(
            action='two_factor_setup_initiated',
            entity_type='user',
            entity_id=user.id,
            user=user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'secret': user.two_factor_secret,
            'qr_code': f"data:image/png;base64,{qr_code_base64}"
        })
    
    @action(detail=False, methods=['post'])
    def verify_2fa(self, request):
        """
        Verify the 2FA code and enable 2FA for the user if correct.
        """
        user = request.user
        code = request.data.get('code')
        
        if not code:
            return Response(
                {'error': 'Verification code is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.two_factor_secret:
            return Response(
                {'error': 'Two-factor authentication not set up.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the TOTP code
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(code):
            # Enable 2FA
            user.two_factor_enabled = True
            user.save(update_fields=['two_factor_enabled'])
            
            # Log 2FA enablement
            AuditLog.log(
                action='two_factor_enabled',
                entity_type='user',
                entity_id=user.id,
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'success': 'Two-factor authentication enabled.'})
        else:
            # Log failed 2FA verification
            AuditLog.log(
                action='two_factor_verification_failed',
                entity_type='user',
                entity_id=user.id,
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response(
                {'error': 'Invalid verification code.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def disable_2fa(self, request):
        """
        Disable 2FA for the current user.
        Requires a verification code to confirm identity.
        """
        user = request.user
        code = request.data.get('code')
        
        if not user.two_factor_enabled:
            return Response(
                {'error': 'Two-factor authentication is not enabled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not code:
            return Response(
                {'error': 'Verification code is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the TOTP code
        totp = pyotp.TOTP(user.two_factor_secret)
        if totp.verify(code):
            # Disable 2FA and clear the secret
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.save(update_fields=['two_factor_enabled', 'two_factor_secret'])
            
            # Log 2FA disablement
            AuditLog.log(
                action='two_factor_disabled',
                entity_type='user',
                entity_id=user.id,
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'success': 'Two-factor authentication disabled.'})
        else:
            return Response(
                {'error': 'Invalid verification code.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for the current authenticated user.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return self.serializer_class
    
    def perform_update(self, serializer):
        try:
            instance = serializer.save()
            
            # Log user update
            AuditLog.log(
                action='user_update',
                entity_type='user',
                entity_id=instance.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success'
            )
        except Exception as e:
            # Log failed user update
            AuditLog.log(
                action='user_update_failed',
                entity_type='user',
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={'error': str(e)}
            )
            raise
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PasswordChangeView(generics.GenericAPIView):
    """
    API endpoint for changing user password.
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']
            
            # Check if current password is correct
            if not user.check_password(current_password):
                return Response(
                    {'current_password': 'Wrong password.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # If 2FA is enabled, require verification for password change
            if user.two_factor_enabled:
                code = request.data.get('code')
                if not code:
                    return Response(
                        {'code': 'Verification code is required for 2FA-enabled accounts.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                totp = pyotp.TOTP(user.two_factor_secret)
                if not totp.verify(code):
                    # Revert the password change
                    user.set_password(current_password)
                    user.save()
                    return Response(
                        {'code': 'Invalid verification code.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Log the password change
            AuditLog.log(
                action='password_change',
                entity_type='user',
                entity_id=user.id,
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Invalidate all refresh tokens
            try:
                RefreshToken.revoke_all_for_user(user)
            except Exception:
                pass
            
            return Response(
                {'success': 'Password updated successfully.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for roles (read-only).
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserBlockViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user blocks.
    """
    serializer_class = UserBlockSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserBlock.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Check if the user is trying to block themselves
        blocked_user_id = serializer.validated_data.get('blocked_user_id')
        if str(blocked_user_id) == str(self.request.user.id):
            raise serializers.ValidationError("You cannot block yourself.")
        
        # Check if the user is trying to block an admin
        try:
            blocked_user = User.objects.get(id=blocked_user_id)
            if blocked_user.is_staff:
                raise serializers.ValidationError("You cannot block administrators.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
        serializer.save(user=self.request.user)
        
        # Log block action
        AuditLog.log(
            action='user_block',
            entity_type='user',
            entity_id=blocked_user_id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def perform_destroy(self, instance):
        blocked_user_id = instance.blocked_user.id
        
        if instance.user != self.request.user:
            raise PermissionDenied("You can only remove your own blocks.")
        
        instance.delete()
        
        # Log unblock action
        AuditLog.log(
            action='user_unblock',
            entity_type='user',
            entity_id=blocked_user_id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
