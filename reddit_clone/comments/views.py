from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Comment
from .serializers import CommentSerializer
from communities.models import CommunityModerator
from security.models import AuditLog
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comments.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Comment.objects.filter(is_deleted=False)
        
        # Filter by post
        post_id = self.request.query_params.get('post', None)
        post_path = self.request.query_params.get('post_path', None)
        
        if post_id:
            queryset = queryset.filter(post__id=post_id)
        elif post_path:
            queryset = queryset.filter(post__path=post_path)
        
        # Filter by parent comment
        parent_id = self.request.query_params.get('parent', None)
        if parent_id:
            if parent_id == 'none':
                # Get top-level comments
                queryset = queryset.filter(parent__isnull=True)
            else:
                # Get replies to a specific comment
                queryset = queryset.filter(parent__id=parent_id)
        
        # Filter by user (username only)
        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(user__username=username)
        
        # Time-based filtering
        time_filter = self.request.query_params.get('time', None)
        if time_filter:
            now = timezone.now()
            if time_filter == 'day':
                # Comments from the last 24 hours
                queryset = queryset.filter(created_at__gte=now - timedelta(days=1))
            elif time_filter == 'week':
                # Comments from the last 7 days
                queryset = queryset.filter(created_at__gte=now - timedelta(days=7))
            elif time_filter == 'month':
                # Comments from the last 30 days
                queryset = queryset.filter(created_at__gte=now - timedelta(days=30))
            elif time_filter == 'year':
                # Comments from the last 365 days
                queryset = queryset.filter(created_at__gte=now - timedelta(days=365))
        
        # Sort
        sort = self.request.query_params.get('sort', 'new')
        if sort == 'top' or sort == 'best':
            # Top/Best: Highest scores first
            queryset = queryset.order_by('-upvote_count', '-created_at')
        elif sort == 'controversial':
            # Controversial: Comments with similar up/down votes
            from django.db.models import F, ExpressionWrapper, FloatField
            from django.db.models.functions import Greatest, Abs
            
            queryset = queryset.annotate(
                controversy=ExpressionWrapper(
                    (F('upvote_count') + F('downvote_count')) / 
                    (Greatest(Abs(F('upvote_count') - F('downvote_count')), 1)),
                    output_field=FloatField()
                )
            ).filter(upvote_count__gt=0, downvote_count__gt=0).order_by('-controversy')
        elif sort == 'hot':
            # Hot: Higher scores with recency factor
            from django.db.models import F, ExpressionWrapper, FloatField, Value
            from django.db.models.functions import Log, Greatest, Extract
            
            queryset = queryset.annotate(
                hours_passed=ExpressionWrapper(
                    # Calculate the age in hours using Extract function in PostgreSQL
                    # Add 0.1 to ensure we never have zero hours
                    Extract(timezone.now() - F('created_at'), 'epoch') / 3600.0 + 0.1,
                    output_field=FloatField()
                ),
                score_diff=Greatest(F('upvote_count') - F('downvote_count'), 1),
                hot_score=ExpressionWrapper(
                    Log(F('score_diff'), 10) / 
                    ((F('hours_passed')) ** 1.5),
                    output_field=FloatField()
                )
            ).order_by('-hot_score')
        elif sort == 'old':
            # Old: Oldest first
            queryset = queryset.order_by('created_at')
        else:
            # New: Most recent first (default)
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def perform_create(self, serializer):
        # Check if the post is locked before allowing comment creation
        post = serializer.validated_data.get('post')
        if post.is_locked:
            raise PermissionDenied(f"Cannot add comments: This post has been locked by a moderator. ")
            
        try:
            comment = serializer.save()
            
            # Send notifications for new comments
            from notifications.models import Notification
            
            # Send notification to post author if this is a direct comment on the post
            if not comment.parent:
                Notification.send_post_reply_notification(comment)
            # Send notification to parent comment author if this is a reply
            else:
                Notification.send_comment_reply_notification(comment)
            
            # Process @mentions in the comment content
            self.process_mentions(comment)
            
            # Log comment creation
            AuditLog.log(
                action='comment_create',
                entity_type='comment',
                entity_id=comment.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'post_id': str(comment.post.id),
                    'parent_id': str(comment.parent.id) if comment.parent else None
                }
            )
        except Exception as e:
            # Log failed comment creation
            post_id = serializer.validated_data.get('post', {}).id if serializer.validated_data.get('post') else 'unknown'
            parent_id = serializer.validated_data.get('parent', {}).id if serializer.validated_data.get('parent') else None
            
            AuditLog.log(
                action='comment_create_failed',
                entity_type='comment',
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'error': str(e),
                    'post_id': str(post_id) if post_id != 'unknown' else 'unknown',
                    'parent_id': str(parent_id) if parent_id else None
                }
            )
            raise
    
    def process_mentions(self, comment):
        """Process @mentions in the comment content and send notifications."""
        import re
        from django.contrib.auth import get_user_model
        from notifications.models import Notification
        
        User = get_user_model()
        
        # Extract all @usernames from the comment text
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, comment.content)
        
        # Send notification to each mentioned user
        for username in mentions:
            try:
                mentioned_user = User.objects.get(username=username)
                Notification.send_mention_notification(
                    mentioned_user=mentioned_user,
                    content_obj=comment,
                    sender=comment.user
                )
            except User.DoesNotExist:
                # Username doesn't exist, skip it
                pass
    
    def perform_update(self, serializer):
        try:
            comment = serializer.save()
            
            # Log comment update
            AuditLog.log(
                action='comment_update',
                entity_type='comment',
                entity_id=comment.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'post_id': str(comment.post.id),
                    'parent_id': str(comment.parent.id) if comment.parent else None
                }
            )
        except Exception as e:
            # Get the comment ID from the URL
            comment_id = self.kwargs.get('pk')
            
            # Log failed comment update
            AuditLog.log(
                action='comment_update_failed',
                entity_type='comment',
                entity_id=comment_id if comment_id else None,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={'error': str(e)}
            )
            raise
    
    def perform_destroy(self, instance):
        try:
            # Log comment deletion
            AuditLog.log(
                action='comment_delete',
                entity_type='comment',
                entity_id=instance.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'post_id': str(instance.post.id),
                    'parent_id': str(instance.parent.id) if instance.parent else None
                }
            )
            
            # Soft delete rather than hard delete
            instance.soft_delete()
        except Exception as e:
            # Log failed comment deletion
            AuditLog.log(
                action='comment_delete_failed',
                entity_type='comment',
                entity_id=instance.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'post_id': str(instance.post.id),
                    'parent_id': str(instance.parent.id) if instance.parent else None,
                    'error': str(e)
                }
            )
            raise
    
    @action(detail=True, methods=['post'])
    def remove(self, request, pk=None):
        comment = self.get_object()
        
        # Check if user is a moderator of the post's community
        is_moderator = CommunityModerator.objects.filter(
            community=comment.post.community,
            user=request.user
        ).exists()
        
        if not is_moderator and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to remove this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason', '')
        comment.remove(request.user, reason)
        
        # Send notification to comment author about the removal
        from notifications.models import Notification
        Notification.send_mod_action_notification(
            user=comment.user,
            community=comment.post.community,
            action=f"Your comment was removed: {reason}",
            admin_user=request.user,
            link_url=f"/post/{comment.post.id}"
        )
        
        # Log comment removal by moderator
        AuditLog.log(
            action='comment_remove',
            entity_type='comment',
            entity_id=comment.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={
                'post_id': str(comment.post.id),
                'reason': reason
            }
        )
        
        return Response({"detail": "Comment removed successfully."})
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        comment = self.get_object()
        
        # Check if user is a moderator of the post's community
        is_moderator = CommunityModerator.objects.filter(
            community=comment.post.community,
            user=request.user
        ).exists()
        
        if not is_moderator and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to restore this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        comment.restore()
        
        # Log comment restoration by moderator
        AuditLog.log(
            action='comment_restore',
            entity_type='comment',
            entity_id=comment.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({"detail": "Comment restored successfully."})
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
