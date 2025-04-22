from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, F, ExpressionWrapper, FloatField, Count, Value, CharField, Exists, OuterRef
from django.db.models.functions import Log, Greatest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from rest_framework.exceptions import PermissionDenied
import os
import io
from PIL import Image
from .models import Post, PostMedia
from .serializers import PostSerializer, PostMediaSerializer
from utils.media_validators import validate_image, validate_video, generate_safe_filename
from communities.models import Community, CommunityMember, CommunityModerator
from security.models import AuditLog
import traceback
import json
import re
import logging
from communities.serializers import CommunitySerializer
from users.models import UserBlock
from .models import Vote, PostImage, PostSave, PostReport
from .serializers import PostCreateSerializer, PostUpdateSerializer, VoteSerializer, PostImageSerializer
from notifications.models import Notification
from utils.ranking_algorithms import calculate_hotness, calculate_trending, calculate_controversy
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
import uuid
import zipfile
import csv


class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint for posts.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Post.objects.filter(is_deleted=False)
        
        # Filter by community
        community_id = self.request.query_params.get('community', None)
        if community_id:
            queryset = queryset.filter(community__id=community_id)
        
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user__id=user_id)
        
        # Filter by flair
        flair_id = self.request.query_params.get('flair', None)
        if flair_id:
            queryset = queryset.filter(flair__id=flair_id)
        
        # Sort
        sort = self.request.query_params.get('sort', 'new')
        if sort == 'hot':
            # Hot: Higher scores with recency factor
            queryset = queryset.annotate(
                hours_passed=ExpressionWrapper(
                    (timezone.now() - F('created_at')) / timedelta(hours=1),
                    output_field=FloatField()
                ),
                hot_score=ExpressionWrapper(
                    Log(Greatest(F('upvote_count') - F('downvote_count'), 1)) / 
                    (Greatest(F('hours_passed'), 2) ** 1.5),
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
                    (Greatest(abs(F('upvote_count') - F('downvote_count')), 1)),
                    output_field=FloatField()
                )
            ).filter(upvote_count__gt=0, downvote_count__gt=0).order_by('-controversy')
        else:
            # New: Most recent first (default)
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def perform_create(self, serializer):
        try:
            post = serializer.save()
            
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
        try:
            # Log post deletion
            AuditLog.log(
                action='post_delete',
                entity_type='post',
                entity_id=instance.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'community_id': str(instance.community.id),
                    'title': instance.title
                }
            )
            
            # Soft delete rather than hard delete
            instance.soft_delete()
        except Exception as e:
            # Log failed post deletion
            AuditLog.log(
                action='post_delete_failed',
                entity_type='post',
                entity_id=instance.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'community_id': str(instance.community.id),
                    'title': instance.title,
                    'error': str(e)
                }
            )
            raise
    
    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
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
    def unlock(self, request, pk=None):
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
    def pin(self, request, pk=None):
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
    def unpin(self, request, pk=None):
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


class PostMediaViewSet(viewsets.ModelViewSet):
    """
    API endpoint for post media.
    """
    serializer_class = PostMediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PostMedia.objects.all()
    
    def create(self, request, *args, **kwargs):
        # Validate required fields
        if 'post' not in request.data:
            return Response(
                {"post": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'media_type' not in request.data:
            return Response(
                {"media_type": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'media_file' not in request.FILES:
            return Response(
                {"media_file": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the post and check permissions
        try:
            post_id = request.data['post']
            post = Post.objects.get(id=post_id)
            
            # Only allow the post author to add media
            if post.user != request.user:
                return Response(
                    {"detail": "You don't have permission to add media to this post."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Post.DoesNotExist:
            return Response(
                {"post": "Post not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate and process the uploaded file
        media_file = request.FILES['media_file']
        media_type = request.data['media_type']
        
        try:
            if media_type == 'image':
                # Validate image file
                validate_image(media_file)
            elif media_type == 'video':
                # Validate video file
                validate_video(media_file)
            else:
                return Response(
                    {"media_type": "Invalid media type. Must be 'image' or 'video'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate a safe filename
            safe_filename = generate_safe_filename(media_file.name)
            
            # Save the file to the specified location
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'posts', str(post.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save the file
            file_path = os.path.join(upload_dir, safe_filename)
            with open(file_path, 'wb+') as destination:
                for chunk in media_file.chunks():
                    destination.write(chunk)
            
            # Create the media object
            media_url = f"{settings.MEDIA_URL}posts/{post.id}/{safe_filename}"
            
            # Create a thumbnail for images
            thumbnail_url = None
            if media_type == 'image':
                # Open the image
                img = Image.open(file_path)
                
                # Create a thumbnail
                img.thumbnail((300, 300))
                
                # Save the thumbnail
                thumb_filename = f"thumb_{safe_filename}"
                thumb_path = os.path.join(upload_dir, thumb_filename)
                img.save(thumb_path)
                
                thumbnail_url = f"{settings.MEDIA_URL}posts/{post.id}/{thumb_filename}"
            
            # Create the media object
            media = PostMedia.objects.create(
                post=post,
                media_type=media_type,
                media_url=media_url,
                thumbnail_url=thumbnail_url,
                order=PostMedia.objects.filter(post=post).count()
            )
            
            # Log media upload
            AuditLog.log(
                action='post_media_upload',
                entity_type='post_media',
                entity_id=media.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={
                    'post_id': str(post.id),
                    'media_type': media_type,
                    'file_size': media_file.size,
                    'original_filename': media_file.name
                }
            )
            
            serializer = self.get_serializer(media)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_destroy(self, instance):
        # Check permissions
        if instance.post.user != self.request.user:
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
        
        # Delete the actual file
        if instance.media_url:
            # Extract the file path from the URL
            file_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'media',
                instance.media_url.replace('media/', '')
            )
            
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete the thumbnail
        if instance.thumbnail_url:
            # Extract the file path from the URL
            thumb_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'media',
                instance.thumbnail_url.replace('media/', '')
            )
            
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
        
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
