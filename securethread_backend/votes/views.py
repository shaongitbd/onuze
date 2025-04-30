from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Vote
from .serializers import VoteSerializer
from posts.models import Post
from comments.models import Comment
from security.models import AuditLog
from notifications.models import Notification


class VoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for votes on posts and comments.
    """
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        This view should return votes filtered by user and content type.
        """
        queryset = Vote.objects.all()
        
        # Filter by user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user__id=user_id)
        
        # Filter by post
        post_id = self.request.query_params.get('post', None)
        if post_id:
            queryset = queryset.filter(post__id=post_id)
        
        # Filter by comment
        comment_id = self.request.query_params.get('comment', None)
        if comment_id:
            queryset = queryset.filter(comment__id=comment_id)
        
        # Filter by vote type
        vote_type = self.request.query_params.get('type', None)
        if vote_type and vote_type in ['up', 'down']:
            queryset = queryset.filter(vote_type=vote_type)
        
        return queryset
    
    def perform_create(self, serializer):
        try:
            vote = serializer.save(user=self.request.user)
            
            # Log vote creation
            entity_type = 'post' if vote.post else 'comment'
            entity_id = vote.post.id if vote.post else vote.comment.id
            
            AuditLog.log(
                action=f'{vote.vote_type}vote_{entity_type}',
                entity_type=entity_type,
                entity_id=entity_id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={'vote_id': str(vote.id)}
            )
            
            # Check for vote milestones and send notifications
            if vote.vote_type == Vote.UPVOTE:
                content_obj = vote.post if vote.content_type == Vote.POST else vote.comment
                if content_obj:
                    # Milestones to check (upvotes)
                    milestones = [10, 50, 100, 500, 1000]
                    
                    # If upvote count hits a milestone exactly, send notification
                    if content_obj.upvote_count in milestones:
                        Notification.send_vote_milestone_notification(
                            content_type=vote.content_type,
                            content_obj=content_obj,
                            milestone=content_obj.upvote_count
            )
        except Exception as e:
            # Determine entity type from serializer data
            has_post = 'post' in serializer.validated_data
            has_comment = 'comment' in serializer.validated_data
            entity_type = 'post' if has_post else 'comment' if has_comment else 'unknown'
            
            # Get entity ID if available
            entity_id = None
            if has_post and serializer.validated_data['post']:
                entity_id = serializer.validated_data['post'].id
            elif has_comment and serializer.validated_data['comment']:
                entity_id = serializer.validated_data['comment'].id
            
            vote_type = serializer.validated_data.get('vote_type', 'unknown')
            
            # Log failed vote creation
            AuditLog.log(
                action=f'{vote_type}vote_{entity_type}_failed',
                entity_type=entity_type,
                entity_id=entity_id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={'error': str(e)}
            )
            raise
    
    def perform_update(self, serializer):
        try:
            vote = serializer.save()
            
            # Log vote update
            entity_type = 'post' if vote.post else 'comment'
            entity_id = vote.post.id if vote.post else vote.comment.id
            
            AuditLog.log(
                action=f'vote_update_{entity_type}',
                entity_type=entity_type,
                entity_id=entity_id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'vote_id': str(vote.id),
                    'vote_type': vote.vote_type
                }
            )
        except Exception as e:
            # Get the vote ID from the URL
            vote_id = self.kwargs.get('pk')
            
            # Log failed vote update
            AuditLog.log(
                action='vote_update_failed',
                entity_type='vote',
                entity_id=vote_id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={'error': str(e)}
            )
            raise
    
    def perform_destroy(self, instance):
        try:
            # Log vote deletion
            entity_type = 'post' if instance.post else 'comment'
            entity_id = instance.post.id if instance.post else instance.comment.id
            
            AuditLog.log(
                action=f'vote_remove_{entity_type}',
                entity_type=entity_type,
                entity_id=entity_id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'vote_id': str(instance.id),
                    'vote_type': instance.vote_type
                }
            )
            
            instance.delete()
        except Exception as e:
            # Log failed vote deletion
            entity_type = 'post' if instance.post else 'comment'
            entity_id = instance.post.id if instance.post else instance.comment.id
            
            AuditLog.log(
                action=f'vote_remove_{entity_type}_failed',
                entity_type=entity_type,
                entity_id=entity_id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'vote_id': str(instance.id),
                    'vote_type': instance.vote_type,
                    'error': str(e)
                }
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


class PostVoteView(generics.GenericAPIView):
    """
    API endpoint for voting on posts.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VoteSerializer
    
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        vote_type = request.data.get('vote_type')
        
        if vote_type not in [Vote.UPVOTE, Vote.DOWNVOTE]:
            return Response({
                'detail': 'Invalid vote type. Must be either 1 (upvote) or -1 (downvote).'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update the vote
        vote = Vote.create_or_update(
            user=request.user,
            content_type=Vote.POST,
            content_id=post_id,
            vote_type=vote_type
        )
        
        # Log vote action
        vote_label = 'upvote' if vote_type == Vote.UPVOTE else 'downvote'
        action_type = 'create' if vote else 'remove'
        
        AuditLog.log(
            action=f'post_{vote_label}_{action_type}',
            entity_type='post',
            entity_id=post_id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='success',
            details={
                'post_title': post.title,
                'vote_type': vote_type
            }
        )
        
        # If vote is None, it means it was toggled off
        if vote is None:
            return Response({
                'detail': f'Your {vote_label} has been removed.',
                'vote_count': post.get_score(),
                'upvote_count': post.upvote_count,
                'downvote_count': post.downvote_count
            })
        
        # Otherwise, vote was created or updated
        serializer = self.get_serializer(vote)
        
        return Response({
            'detail': f'Post has been {vote_label}d.',
            'vote': serializer.data,
            'vote_count': post.get_score(),
            'upvote_count': post.upvote_count,
            'downvote_count': post.downvote_count
        })
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CommentVoteView(generics.GenericAPIView):
    """
    API endpoint for voting on comments.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VoteSerializer
    
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        vote_type = request.data.get('vote_type')
        
        if vote_type not in [Vote.UPVOTE, Vote.DOWNVOTE]:
            return Response({
                'detail': 'Invalid vote type. Must be either 1 (upvote) or -1 (downvote).'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or update the vote
        vote = Vote.create_or_update(
            user=request.user,
            content_type=Vote.COMMENT,
            content_id=comment_id,
            vote_type=vote_type
        )
        
        # Log vote action
        vote_label = 'upvote' if vote_type == Vote.UPVOTE else 'downvote'
        action_type = 'create' if vote else 'remove'
        
        AuditLog.log(
            action=f'comment_{vote_label}_{action_type}',
            entity_type='comment',
            entity_id=comment_id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='success',
            details={
                'comment_preview': comment.content[:50] + '...' if len(comment.content) > 50 else comment.content,
                'vote_type': vote_type
            }
        )
        
        # If vote is None, it means it was toggled off
        if vote is None:
            return Response({
                'detail': f'Your {vote_label} has been removed.',
                'vote_count': comment.get_score(),
                'upvote_count': comment.upvote_count,
                'downvote_count': comment.downvote_count
            })
        
        # Otherwise, vote was created or updated
        serializer = self.get_serializer(vote)
        
        return Response({
            'detail': f'Comment has been {vote_label}d.',
            'vote': serializer.data,
            'vote_count': comment.get_score(),
            'upvote_count': comment.upvote_count,
            'downvote_count': comment.downvote_count
        })
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PostVoteByPathView(generics.GenericAPIView):
    """
    API endpoint for voting on posts using path-based lookup.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VoteSerializer
    
    def post(self, request, post_path):
        post = get_object_or_404(Post, path=post_path)
        vote_type = request.data.get('vote_type')
        
        if vote_type not in [Vote.UPVOTE, Vote.DOWNVOTE]:
            return Response({
                'detail': 'Invalid vote type. Must be either 1 (upvote) or -1 (downvote).'
            }, status=status.HTTP_400_BAD_REQUEST)
        print(post.id)
        # Create or update the vote
        vote = Vote.create_or_update(
            user=request.user,
            content_type=Vote.POST,
            content_id=post.id,
            vote_type=vote_type
        )
        
        # Log vote action
        vote_label = 'upvote' if vote_type == Vote.UPVOTE else 'downvote'
        action_type = 'create' if vote else 'remove'
        
        AuditLog.log(
            action=f'post_{vote_label}_{action_type}',
            entity_type='post',
            entity_id=post.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            status='success',
            details={
                'post_title': post.title,
                'vote_type': vote_type
            }
        )
        
        # If vote is None, it means it was toggled off
        if vote is None:
            return Response({
                'detail': f'Your {vote_label} has been removed.',
                'vote_count': post.get_score(),
                'upvote_count': post.upvote_count,
                'downvote_count': post.downvote_count
            })
        
        # Otherwise, vote was created or updated
        serializer = self.get_serializer(vote)
        
        return Response({
            'detail': f'Post has been {vote_label}d.',
            'vote': serializer.data,
            'vote_count': post.get_score(),
            'upvote_count': post.upvote_count,
            'downvote_count': post.downvote_count
        })
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
