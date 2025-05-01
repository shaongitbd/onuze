from rest_framework import serializers
from users.serializers import UserBriefSerializer
from .models import Notification
from django.contrib.contenttypes.models import ContentType


class ContentTypeField(serializers.Field):
    """
    Custom field to handle content_type, whether it's a string or ContentType instance
    """
    def to_representation(self, value):
        if isinstance(value, ContentType):
            return {
                'app_label': value.app_label,
                'model': value.model
            }
        elif isinstance(value, str):
            # Handle if it's a string
            return {
                'name': value
            }
        return None


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    sender = UserBriefSerializer(read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    content_type = ContentTypeField(read_only=True)
    content_id = serializers.UUIDField(read_only=True)
    id = serializers.UUIDField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user_id', 'sender', 'notification_type', 
            'content_type', 'content_id', 'message', 
            'is_read', 'created_at', 'link_url'
        ]
        read_only_fields = [
            'id', 'user_id', 'sender', 'notification_type', 
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