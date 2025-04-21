from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Vote
from .serializers import VoteSerializer
from posts.models import Post
from comments.models import Comment
from security.models import AuditLog


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
    
    @action(detail=False, methods=['post'])
    def upvote_post(self, request):
        post_id = request.data.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        
        # Check if a vote already exists
        existing_vote = Vote.objects.filter(
            user=request.user,
            post=post
        ).first()
        
        if existing_vote:
            if existing_vote.vote_type == 'up':
                # If already upvoted, remove the vote (toggle off)
                existing_vote.delete()
                
                # Log vote removal
                AuditLog.log(
                    action='upvote_post_remove',
                    entity_type='post',
                    entity_id=post.id,
                    user=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'post_title': post.title}
                )
                
                return Response({'detail': 'Upvote removed.'})
            else:
                # If previously downvoted, change to upvote
                existing_vote.vote_type = 'up'
                existing_vote.save()
                
                # Log vote update
                AuditLog.log(
                    action='downvote_to_upvote_post',
                    entity_type='post',
                    entity_id=post.id,
                    user=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'post_title': post.title}
                )
                
                return Response({'detail': 'Downvote changed to upvote.'})
        else:
            # Create a new upvote
            vote = Vote.objects.create(
                user=request.user,
                post=post,
                vote_type='up'
            )
            
            # Log new upvote
            AuditLog.log(
                action='upvote_post_new',
                entity_type='post',
                entity_id=post.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'post_title': post.title}
            )
            
            return Response({'detail': 'Post upvoted.'})
    
    @action(detail=False, methods=['post'])
    def downvote_post(self, request):
        post_id = request.data.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        
        # Check if a vote already exists
        existing_vote = Vote.objects.filter(
            user=request.user,
            post=post
        ).first()
        
        if existing_vote:
            if existing_vote.vote_type == 'down':
                # If already downvoted, remove the vote (toggle off)
                existing_vote.delete()
                
                # Log vote removal
                AuditLog.log(
                    action='downvote_post_remove',
                    entity_type='post',
                    entity_id=post.id,
                    user=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'post_title': post.title}
                )
                
                return Response({'detail': 'Downvote removed.'})
            else:
                # If previously upvoted, change to downvote
                existing_vote.vote_type = 'down'
                existing_vote.save()
                
                # Log vote update
                AuditLog.log(
                    action='upvote_to_downvote_post',
                    entity_type='post',
                    entity_id=post.id,
                    user=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'post_title': post.title}
                )
                
                return Response({'detail': 'Upvote changed to downvote.'})
        else:
            # Create a new downvote
            vote = Vote.objects.create(
                user=request.user,
                post=post,
                vote_type='down'
            )
            
            # Log new downvote
            AuditLog.log(
                action='downvote_post_new',
                entity_type='post',
                entity_id=post.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'post_title': post.title}
            )
            
            return Response({'detail': 'Post downvoted.'})
    
    @action(detail=False, methods=['post'])
    def upvote_comment(self, request):
        comment_id = request.data.get('comment_id')
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Check if a vote already exists
        existing_vote = Vote.objects.filter(
            user=request.user,
            comment=comment
        ).first()
        
        if existing_vote:
            if existing_vote.vote_type == 'up':
                # If already upvoted, remove the vote (toggle off)
                existing_vote.delete()
                
                # Log vote removal
                AuditLog.log(
                    action='upvote_comment_remove',
                    entity_type='comment',
                    entity_id=comment.id,
                    user=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'post_id': str(comment.post.id)}
                )
                
                return Response({'detail': 'Upvote removed.'})
            else:
                # If previously downvoted, change to upvote
                existing_vote.vote_type = 'up'
                existing_vote.save()
                
                # Log vote update
                AuditLog.log(
                    action='downvote_to_upvote_comment',
                    entity_type='comment',
                    entity_id=comment.id,
                    user=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'post_id': str(comment.post.id)}
                )
                
                return Response({'detail': 'Downvote changed to upvote.'})
        else:
            # Create a new upvote
            vote = Vote.objects.create(
                user=request.user,
                comment=comment,
                vote_type='up'
            )
            
            # Log new upvote
            AuditLog.log(
                action='upvote_comment_new',
                entity_type='comment',
                entity_id=comment.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'post_id': str(comment.post.id)}
            )
            
            return Response({'detail': 'Comment upvoted.'})
    
    @action(detail=False, methods=['post'])
    def downvote_comment(self, request):
        comment_id = request.data.get('comment_id')
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Check if a vote already exists
        existing_vote = Vote.objects.filter(
            user=request.user,
            comment=comment
        ).first()
        
        if existing_vote:
            if existing_vote.vote_type == 'down':
                # If already downvoted, remove the vote (toggle off)
                existing_vote.delete()
                
                # Log vote removal
                AuditLog.log(
                    action='downvote_comment_remove',
                    entity_type='comment',
                    entity_id=comment.id,
                    user=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'post_id': str(comment.post.id)}
                )
                
                return Response({'detail': 'Downvote removed.'})
            else:
                # If previously upvoted, change to downvote
                existing_vote.vote_type = 'down'
                existing_vote.save()
                
                # Log vote update
                AuditLog.log(
                    action='upvote_to_downvote_comment',
                    entity_type='comment',
                    entity_id=comment.id,
                    user=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    details={'post_id': str(comment.post.id)}
                )
                
                return Response({'detail': 'Upvote changed to downvote.'})
        else:
            # Create a new downvote
            vote = Vote.objects.create(
                user=request.user,
                comment=comment,
                vote_type='down'
            )
            
            # Log new downvote
            AuditLog.log(
                action='downvote_comment_new',
                entity_type='comment',
                entity_id=comment.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'post_id': str(comment.post.id)}
            )
            
            return Response({'detail': 'Comment downvoted.'})
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
