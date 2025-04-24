from rest_framework import serializers
from .models import (
    Community, CommunityMember, CommunityModerator, 
    CommunityRule, Flair, CommunitySetting
)
from users.serializers import UserSerializer


class CommunitySerializer(serializers.ModelSerializer):
    """Serializer for the Community model."""
    member_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Community
        fields = [
            'id', 'name', 'path', 'description', 'created_at', 'created_by',
            'sidebar_content', 'banner_image', 'icon_image',
            'is_private', 'member_count', 'is_nsfw'
        ]
        read_only_fields = ['id', 'path', 'created_at', 'created_by', 'member_count']


class CommunityMemberSerializer(serializers.ModelSerializer):
    """Serializer for the CommunityMember model."""
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = CommunityMember
        fields = [
            'id', 'community', 'user', 'user_details', 'joined_at',
            'is_banned', 'ban_reason', 'banned_until', 'banned_by'
        ]
        read_only_fields = ['id', 'joined_at', 'banned_by']


class CommunityModeratorSerializer(serializers.ModelSerializer):
    """Serializer for the CommunityModerator model."""
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = CommunityModerator
        fields = [
            'id', 'community', 'user', 'user_details',
            'appointed_at', 'appointed_by', 'permissions'
        ]
        read_only_fields = ['id', 'appointed_at']


class CommunityRuleSerializer(serializers.ModelSerializer):
    """Serializer for the CommunityRule model."""
    
    class Meta:
        model = CommunityRule
        fields = [
            'id', 'community', 'title', 'description',
            'created_at', 'created_by', 'order'
        ]
        read_only_fields = ['id', 'created_at', 'created_by']


class FlairSerializer(serializers.ModelSerializer):
    """Serializer for the Flair model."""
    
    class Meta:
        model = Flair
        fields = [
            'id', 'community', 'name', 'background_color',
            'text_color', 'created_at', 'created_by', 'is_mod_only'
        ]
        read_only_fields = ['id', 'created_at', 'created_by']


class CommunitySettingSerializer(serializers.ModelSerializer):
    """Serializer for the CommunitySetting model."""
    
    class Meta:
        model = CommunitySetting
        fields = [
            'id', 'community', 'key', 'value', 'value_type',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Return the typed value."""
        ret = super().to_representation(instance)
        ret['typed_value'] = instance.get_typed_value()
        return ret 