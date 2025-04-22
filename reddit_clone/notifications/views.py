from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db.models import Count
from .models import Notification
from .serializers import (
    NotificationSerializer, NotificationUpdateSerializer,
    NotificationCountSerializer
)
from security.models import AuditLog


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        This view should return a list of all notifications
        for the currently authenticated user.
        """
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # Filter by read status if provided
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            is_read = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read)
        
        # Filter by notification type if provided
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Mark as read when retrieved individually
        if not instance.is_read:
            instance.mark_as_read()
            
            # Log notification read
            AuditLog.log(
                action='notification_read',
                entity_type='notification',
                entity_id=instance.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'notification_type': instance.notification_type}
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Use the update serializer which only allows changing is_read
        serializer = NotificationUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Log notification status update
        status_change = "read" if serializer.validated_data.get('is_read', False) else "unread"
        AuditLog.log(
            action=f'notification_mark_{status_change}',
            entity_type='notification',
            entity_id=instance.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'notification_type': instance.notification_type}
        )
        
        return Response(self.get_serializer(instance).data)
    
    def perform_update(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        
        # Log notification read
        AuditLog.log(
            action='notification_mark_read',
            entity_type='notification',
            entity_id=notification.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'notification_type': notification.notification_type}
        )
        
        return Response({'status': 'notification marked as read'})
    
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_unread()
        
        # Log notification unread
        AuditLog.log(
            action='notification_mark_unread',
            entity_type='notification',
            entity_id=notification.id,
            user=request.user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'notification_type': notification.notification_type}
        )
        
        return Response({'status': 'notification marked as unread'})
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class NotificationCountView(generics.GenericAPIView):
    """
    API endpoint for getting notification counts.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationCountSerializer
    
    def get(self, request):
        user = request.user
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        total_count = Notification.objects.filter(user=user).count()
        
        data = {
            'unread_count': unread_count,
            'total_count': total_count
        }
        
        serializer = self.get_serializer(data)
        return Response(serializer.data)


class MarkAllReadView(APIView):
    """
    API endpoint for marking all notifications as read.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        count = Notification.objects.filter(user=user, is_read=False).update(is_read=True)
        
        # Log mark all read
        AuditLog.log(
            action='notification_mark_all_read',
            entity_type='user',
            entity_id=user.id,
            user=user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'count': count}
        )
        
        return Response({
            'status': 'success',
            'message': f'Marked {count} notifications as read.'
        })
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
