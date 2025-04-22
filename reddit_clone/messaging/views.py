from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from users.models import User
from .models import PrivateMessage
from .serializers import PrivateMessageSerializer
from security.models import AuditLog
from django.utils import timezone


class PrivateMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for private messages.
    Handles listing inbox/sent, retrieving, sending, and deleting messages.
    """
    serializer_class = PrivateMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Filter based on inbox or sent
        message_type = self.request.query_params.get('type', 'inbox')
        
        if message_type == 'sent':
            # Sent messages: User is the sender, not deleted by sender
            return PrivateMessage.objects.filter(sender=user, is_deleted_by_sender=False).order_by('-created_at')
        else:
            # Inbox (default): User is the recipient, not deleted by recipient
            return PrivateMessage.objects.filter(recipient=user, is_deleted_by_recipient=False).order_by('-created_at')
    
    def perform_create(self, serializer):
        try:
            message = serializer.save()
            
            # Log message sent
            AuditLog.log(
                action='private_message_sent',
                entity_type='private_message',
                entity_id=message.id,
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'recipient_id': str(message.recipient.id)
                }
            )
            
            # TODO: Optionally send a notification to the recipient
            
        except Exception as e:
            AuditLog.log(
                action='private_message_sent_failed',
                entity_type='private_message',
                user=self.request.user,
                ip_address=self.get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                status='failed',
                details={
                    'recipient_id': str(serializer.validated_data.get('recipient_id')),
                    'error': str(e)
                }
            )
            raise
    
    def retrieve(self, request, *args, **kwargs):
        """
        Mark message as read when retrieved.
        """
        instance = self.get_object()
        
        # Mark as read if the user is the recipient
        if instance.recipient == request.user:
            instance.mark_as_read()
            
            # Log message read
            AuditLog.log(
                action='private_message_read',
                entity_type='private_message',
                entity_id=instance.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={
                    'sender_id': str(instance.sender.id)
                }
            )
            
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_destroy(self, instance):
        """
        Soft delete the message for the requesting user.
        """
        user = self.request.user
        deleted = False
        action_log = 'private_message_delete'
        
        try:
            if instance.sender == user:
                instance.mark_as_deleted_by_sender()
                deleted = True
            elif instance.recipient == user:
                instance.mark_as_deleted_by_recipient()
                deleted = True
            
            if deleted:
                # Log message delete
                AuditLog.log(
                    action=action_log,
                    entity_type='private_message',
                    entity_id=instance.id,
                    user=user,
                    ip_address=self.get_client_ip(self.request),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
                    status='success',
                    details={
                        'deleted_by': 'sender' if instance.sender == user else 'recipient'
                    }
                )
            else:
                # User is not sender or recipient
                raise PermissionDenied("You do not have permission to delete this message.")
                
        except Exception as e:
            AuditLog.log(
                action=f'{action_log}_failed',
                entity_type='private_message',
                entity_id=instance.id,
                user=user,
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


class ConversationView(generics.ListAPIView):
    """
    API endpoint for viewing a conversation between the current user and another user.
    """
    serializer_class = PrivateMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user1 = self.request.user
        user2_id = self.kwargs.get('user_id')
        
        user2 = get_object_or_404(User, id=user2_id)
        
        # Get conversation using the model method
        return PrivateMessage.get_conversation(user1, user2)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Mark messages as read for the current user in this conversation
        user = request.user
        updated_count = PrivateMessage.objects.filter(
            recipient=user, 
            sender_id=self.kwargs.get('user_id'), 
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        # Log conversation read
        if updated_count > 0:
            AuditLog.log(
                action='conversation_read',
                entity_type='user',
                entity_id=self.kwargs.get('user_id'),
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status='success',
                details={'messages_read': updated_count}
            )
        
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UnreadCountView(generics.GenericAPIView):
    """
    API endpoint for getting the count of unread private messages.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        unread_count = PrivateMessage.get_unread_count(user)
        return Response({'unread_count': unread_count})
