from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, F, ExpressionWrapper, FloatField, Count, Value, CharField, Exists, OuterRef, DurationField, Func
from django.db.models.functions import Log, Greatest, Now, Abs
from django.db.models.expressions import RawSQL
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from rest_framework.exceptions import PermissionDenied, NotFound
import os
import io
from PIL import Image
from .models import Post, PostMedia, PostSave, PostImage, Vote
from .serializers import PostSerializer, PostMediaSerializer, PostImageSerializer
from utils.media_validators import validate_image, validate_video, generate_safe_filename, ValidationError
from communities.models import Community, CommunityMember, CommunityModerator, Flair, CommunityRule
from security.models import AuditLog
import traceback
import json
import re
import logging
from communities.serializers import CommunitySerializer
from users.models import UserBlock, User
from notifications.models import Notification
from utils.ranking_algorithms import calculate_hotness, calculate_trending, calculate_controversy
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
import uuid
import zipfile
import csv
from core.permissions import IsOwnerOrReadOnly
from rest_framework import serializers

# Configure logger
logger = logging.getLogger('django')


class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint for posts.
    Handles listing, creation, retrieval, update, deletion, and custom actions.
    Uses path for detail lookups.
    """
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrReadOnly]
    lookup_field = 'path'
    lookup_url_kwarg = 'path'
    
    def get_permissions(self):
        """
        Override to allow moderator actions without the IsOwnerOrReadOnly restriction.
        """
        if self.action in ['pin', 'unpin', 'lock', 'unlock', 'destroy']:
            # For moderator actions, only require authentication
            # The specific permission checks happen inside each action method
            return [permissions.IsAuthenticated()]
        # For other actions, use the default permission_classes
        return [permission() for permission in self.permission_classes]
    
    def get_queryset(self):
        queryset = Post.objects.filter(is_deleted=False)
        
        # Filter by community (allow both ID and path)
        community_id = self.request.query_params.get('community', None)
        community_path = self.request.query_params.get('community_path', None)
        if community_id:
            queryset = queryset.filter(community__id=community_id)
        elif community_path:
            queryset = queryset.filter(community__path=community_path)
        
        # Filter by user (username only)
        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(user__username=username)
        
        # Filter by flair
        flair_id = self.request.query_params.get('flair', None)
        if flair_id:
            queryset = queryset.filter(flair__id=flair_id)
        
        # Time-based filtering
        time_filter = self.request.query_params.get('time', None)
        if time_filter:
            now = timezone.now()
            if time_filter == 'day':
                # Posts from the last 24 hours
                queryset = queryset.filter(created_at__gte=now - timedelta(days=1))
            elif time_filter == 'week':
                # Posts from the last 7 days
                queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
            elif time_filter == 'month':
                # Posts from the last 30 days
                queryset = queryset.filter(created_at__gte=now - timedelta(days=30))
            elif time_filter == 'year':
                # Posts from the last 365 days
                queryset = queryset.filter(created_at__gte=now - timedelta(days=365))
        
        # Sort
        sort = self.request.query_params.get('sort', 'new')
        if sort == 'hot':
            # Hot: Higher scores with recency factor
            queryset = queryset.annotate(
                # Calculate hours since post creation using epoch extraction
                hours_passed=ExpressionWrapper(
                    Func(
                        Now() - F('created_at'),
                        function='EXTRACT',
                        template="EXTRACT(EPOCH FROM %(expressions)s)",
                        output_field=FloatField()
                    ) / Value(3600),
                    output_field=FloatField()
                ),
                hot_score=ExpressionWrapper(
                    Log(10, Greatest(F('upvote_count') - F('downvote_count'), 1)) / 
                    (Greatest(F('hours_passed'), 2) ** 1.5), # Use the calculated hours_passed
                    output_field=FloatField()
                )
            ).order_by('-hot_score')
        elif sort == 'top':
            # Top: Highest scores first
            queryset = queryset.order_by('-upvote_count', '-created_at')
        elif sort == 'controversial':
            # Controversial: Posts with similar up/down votes
            queryset = queryset.annotate(
                controversy=ExpressionWrapper(
                    (F('upvote_count') + F('downvote_count')) / 
                    Greatest(
                        Abs(F('upvote_count') - F('downvote_count')),
                        Value(1)
                    ),
                    output_field=FloatField()
                )
            ).filter(upvote_count__gt=0, downvote_count__gt=0).order_by('-controversy')
        else:
            # New: Most recent first (default)
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def perform_create(self, serializer):
        try:
            # Check if user is banned from the community
            community = serializer.validated_data.get('community')
            user = self.request.user
            
            # Check if member is banned
            try:
                member = CommunityMember.objects.get(community=community, user=user)
                if member.is_banned_now():
                    # Get ban details for the error message
                    ban_reason = member.ban_reason or "No reason provided"
                    ban_expiry = "permanently" if not member.banned_until else f"until {member.banned_until.strftime('%Y-%m-%d')}"
                    raise PermissionDenied(f"You are banned from this community {ban_expiry}. Reason: {ban_reason}")
            except CommunityMember.DoesNotExist:
                # If not a member, they're not banned, so we can continue
                pass
            
            post = serializer.save()
            
            # Process @mentions in the post content
            self.process_mentions(post)
            
            # Log post creation
            AuditLog.log(
                action='post_create',
                entity_type='post',
                entity_id=post.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'community_id': str(post.community.id),
                    'title': post.title
                }
            )
        except Exception as e:
            # Log failed post creation
            AuditLog.log(
                action='post_create_failed',
                entity_type='post',
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'error': str(e),
                    'community_id': str(serializer.validated_data.get('community').id) if serializer.validated_data.get('community') else 'unknown',
                    'title': serializer.validated_data.get('title', 'unknown')
                }
            )
            raise
    
    def perform_update(self, serializer):
        try:
            post = serializer.save()
            
            # Log post update
            AuditLog.log(
                action='post_update',
                entity_type='post',
                entity_id=post.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'community_id': str(post.community.id),
                    'title': post.title
                }
            )
        except Exception as e:
            # Get the post ID from the URL
            post_id = self.kwargs.get('pk')
            
            # Log failed post update
            AuditLog.log(
                action='post_update_failed',
                entity_type='post',
                entity_id=post_id if post_id else None,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'error': str(e)
                }
            )
            raise
    
    def perform_destroy(self, instance):
        """
        Delete a post and log the action.
        """
        # Check if user is the post owner, a moderator of the community, or an admin
        user = self.request.user
        is_moderator = instance.community.moderators.filter(id=user.id).exists()
        is_admin = user.is_staff or user.is_superuser
        is_owner = instance.user == user
        
        if is_owner or is_moderator or is_admin:
            # Log the post deletion action
            action_details = {
                'post_id': instance.id,
                'post_title': instance.title,
                'community_name': instance.community.name,
                'action_by': user.username,
                'action_type': 'delete'
            }
            
            # Include who deleted it (self, mod, admin)
            if is_owner:
                action_details['deleted_by'] = 'owner'
            elif is_moderator:
                action_details['deleted_by'] = 'moderator'
            elif is_admin:
                action_details['deleted_by'] = 'admin'
                
            # Log the action
            logger.info(f"Post deleted: {action_details}")
            
            # Send notification to the post author if deleted by mod or admin (not by self)
            if (is_moderator or is_admin) and not is_owner:
                # Get the deleted user description
                deleted_by_type = "admin" if is_admin else "moderator"
                
                # Send notification to post author
                Notification.send_mod_action_notification(
                    user=instance.user,
                    community=instance.community,
                    action=f"Your post '{instance.title}' was deleted by a {deleted_by_type}",
                    admin_user=user,
                    link_url=f"/c/{instance.community.path}"  # Link to community since post will be gone
                )
            
            # Perform the deletion
            super().perform_destroy(instance)
        else:
            # This shouldn't be reached due to the permission classes,
            # but just in case
            raise PermissionDenied("You do not have permission to delete this post.")
    
    @action(detail=True, methods=['post'])
    def lock(self, request, path=None):
        post = self.get_object()
        
        # Check if user is a moderator of the community
        is_moderator = CommunityModerator.objects.filter(
            community=post.community,
            user=request.user
        ).exists()
        
        if not is_moderator and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to lock this post."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason', '')
        post.lock(request.user, reason)
        
        # Send notification to post author
        Notification.send_mod_action_notification(
            user=post.user,
            community=post.community,
            action=f"Your post '{post.title}' was locked: {reason}",
            admin_user=request.user,
            link_url=f"/c/{post.community.path}/post/{post.path}"
        )
        
        # Log post lock
        AuditLog.log(
            action='post_lock',
            entity_type='post',
            entity_id=post.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={
                'community_id': str(post.community.id),
                'reason': reason
            }
        )
        
        return Response({"detail": "Post locked successfully."})
    
    @action(detail=True, methods=['post'])
    def unlock(self, request, path=None):
        post = self.get_object()
        
        # Check if user is a moderator of the community
        is_moderator = CommunityModerator.objects.filter(
            community=post.community,
            user=request.user
        ).exists()
        
        if not is_moderator and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to unlock this post."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post.unlock()
        
        # Send notification to post author
        Notification.send_mod_action_notification(
            user=post.user,
            community=post.community,
            action=f"Your post '{post.title}' has been unlocked",
            admin_user=request.user,
            link_url=f"/c/{post.community.path}/post/{post.path}"
        )
        
        # Log post unlock
        AuditLog.log(
            action='post_unlock',
            entity_type='post',
            entity_id=post.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({"detail": "Post unlocked successfully."})
    
    @action(detail=True, methods=['post'])
    def pin(self, request, path=None):
        post = self.get_object()
        
        # Check if user is a moderator of the community
        is_moderator = CommunityModerator.objects.filter(
            community=post.community,
            user=request.user
        ).exists()
        
        if not is_moderator and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to pin this post."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post.pin()
        
        # Send notification to post author
        Notification.send_mod_action_notification(
            user=post.user,
            community=post.community,
            action=f"Your post '{post.title}' was pinned to the top of {post.community.name}",
            admin_user=request.user,
            link_url=f"/c/{post.community.path}/post/{post.path}"
        )
        
        # Log post pin
        AuditLog.log(
            action='post_pin',
            entity_type='post',
            entity_id=post.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({"detail": "Post pinned successfully."})
    
    @action(detail=True, methods=['post'])
    def unpin(self, request, path=None):
        post = self.get_object()
        
        # Check if user is a moderator of the community
        is_moderator = CommunityModerator.objects.filter(
            community=post.community,
            user=request.user
        ).exists()
        
        if not is_moderator and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to unpin this post."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post.unpin()
        
        # Send notification to post author
        Notification.send_mod_action_notification(
            user=post.user,
            community=post.community,
            action=f"Your post '{post.title}' is no longer pinned",
            admin_user=request.user,
            link_url=f"/c/{post.community.path}/post/{post.path}"
        )
        
        # Log post unpin
        AuditLog.log(
            action='post_unpin',
            entity_type='post',
            entity_id=post.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({"detail": "Post unpinned successfully."})
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def process_mentions(self, post):
        """Process @mentions in the post content and send notifications."""
        import re
        from django.contrib.auth import get_user_model
        from notifications.models import Notification
        
        User = get_user_model()
        
        # Skip if no text content
        if not post.content:
            return
        
        # Extract all @usernames from the post text
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, post.content)
        
        # Send notification to each mentioned user
        for username in mentions:
            try:
                mentioned_user = User.objects.get(username=username)
                Notification.send_mention_notification(
                    mentioned_user=mentioned_user,
                    content_obj=post,
                    sender=post.user
                )
            except User.DoesNotExist:
                # Username doesn't exist, skip it
                pass


class PostMediaViewSet(viewsets.ModelViewSet):
    """
    API endpoint for post media.
    Creation is handled by PostSerializer.
    This viewset can be used for listing or deleting media.
    """
    serializer_class = PostMediaSerializer
    # Adjust permissions as needed, maybe only owner can delete?
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Get post_pk from the URL, provided by the nested router
        post_pk = self.kwargs.get('post_pk')
        if post_pk:
            try:
                # Optional: Check if post exists and user has permission to view?
                post = Post.objects.get(id=post_pk)
                # Add permission checks if necessary, e.g., is community public/private
                return PostMedia.objects.filter(post=post)
            except Post.DoesNotExist:
                return PostMedia.objects.none()
        return PostMedia.objects.none()
    
    # perform_create is no longer needed here, creation happens in PostSerializer
    # def perform_create(self, serializer):
    #    ... (removed) ...
    
    def perform_destroy(self, instance):
        # Check permissions - only post owner should delete media?
        if instance.post.user != self.request.user:
            # Maybe allow moderators too? Add logic here if needed.
            raise PermissionDenied("You don't have permission to delete this media.")
        
        # Log media deletion
        AuditLog.log(
            action='post_media_delete',
            entity_type='post_media',
            entity_id=instance.id,
            user=self.request.user,
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={
                'post_id': str(instance.post.id),
                'media_type': instance.media_type,
                'media_url': instance.media_url
            }
        )
        
        # TODO: Implement deletion from Bunny.net using storage API
        try:
            from storage import post_image_storage # Assuming media uses this storage
            # Construct the path used during upload (requires consistent logic)
            # This is tricky because the UUID was generated during upload.
            # We might need to store the relative path in PostMedia model or parse the URL.
            # For now, let's assume we can get the path from the URL
            if instance.media_url.startswith(post_image_storage.base_url):
                 relative_path = instance.media_url[len(post_image_storage.base_url):]
                 # Ensure location prefix is included if needed
                 full_path = post_image_storage._get_full_path(relative_path)
                 post_image_storage.delete(full_path)
                 # Also delete thumbnail if exists and logic is implemented
        except Exception as e:
            # Log error but proceed with DB deletion
            logger.error(f"Error deleting file from Bunny.net for PostMedia {instance.id}: {e}", exc_info=True)
        
        # Delete the database entry
        instance.delete()
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
