from rest_framework import serializers
from users.serializers import UserBriefSerializer
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    sender = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'sender', 'notification_type', 
            'content_type', 'content_id', 'message', 
            'is_read', 'created_at', 'link_url'
        ]
        read_only_fields = [
            'id', 'user', 'sender', 'notification_type', 
            'content_type', 'content_id', 'message', 
            'created_at', 'link_url'
        ]


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating notifications.
    Used by internal services, not exposed to the API.
    """
    class Meta:
        model = Notification
        fields = [
            'user', 'sender', 'notification_type', 
            'content_type', 'content_id', 'message',
            'link_url'
        ]


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating notifications.
    Only allows marking as read/unread.
    """
    class Meta:
        model = Notification
        fields = ['is_read']


class NotificationCountSerializer(serializers.Serializer):
    """
    Serializer for returning notification counts.
    """
    unread_count = serializers.IntegerField(read_only=True)
    total_count = serializers.IntegerField(read_only=True) 