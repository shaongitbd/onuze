from rest_framework import serializers
from .models import (
    Community, CommunityMember, CommunityModerator, 
    CommunityRule, Flair, CommunitySetting
)

# Add a brief serializer for Communities to avoid circular imports
class CommunityBriefSerializer(serializers.ModelSerializer):
    """Simplified serializer for Community model to avoid circular imports."""
    class Meta:
        model = Community
        fields = ['id', 'name', 'path', 'icon_image']
        read_only_fields = ['id', 'name', 'path', 'icon_image']


class CommunitySerializer(serializers.ModelSerializer):
    """Serializer for the Community model."""
    member_count = serializers.IntegerField(read_only=True)
    is_member = serializers.SerializerMethodField(read_only=True)
    moderators = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Community
        fields = [
            'id', 'name', 'path', 'description', 'created_at', 'created_by',
            'sidebar_content', 'banner_image', 'icon_image',
            'is_private', 'member_count', 'is_nsfw', 'is_member', 'moderators'
        ]
        read_only_fields = ['id', 'path', 'created_at', 'created_by', 'member_count', 'is_member', 'moderators']
    
    def validate_name(self, value):
        """
        Validate that community name contains only lowercase a-z letters.
        """
        import re
        if not re.match(r'^[a-z]+$', value.lower()):
            raise serializers.ValidationError(
                "Community name must contain only lowercase a-z characters, no spaces, numbers, or special characters."
            )
        
        # Check if a community with this name already exists
        # This is needed because the lowercase conversion might cause conflicts
        if Community.objects.filter(name=value.lower()).exists():
            raise serializers.ValidationError(
                "A community with this name already exists. Community names must be unique."
            )
            
        # Check if a community with this path would already exist
        from django.utils.text import slugify
        slug = slugify(value.lower())
        if Community.objects.filter(path=slug).exists():
            raise serializers.ValidationError(
                f"A community with the path '{slug}' already exists. Please choose a different name."
            )
            
        return value.lower()  # Ensure the name is lowercase
    
    def get_is_member(self, obj):
        """Check if the current user is a member of the community."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommunityMember.objects.filter(
                community=obj,
                user=request.user,
                is_approved=True
            ).exists()
        return False
    
    def get_moderators(self, obj):
        """Get the list of moderators for the community."""
        # Fetch all moderators for this community
        moderators = CommunityModerator.objects.filter(community=obj)
        
        # Return a simplified representation with essential moderator info
        return [{
            'id': mod.id,
            'user_id': str(mod.user.id),
            'username': mod.user.username,
            'is_owner': mod.is_owner,
            'appointed_at': mod.appointed_at
        } for mod in moderators]


class CommunityMemberSerializer(serializers.ModelSerializer):
    """Serializer for the CommunityMember model."""
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CommunityMember
        fields = [
            'id', 'community', 'user', 'user_details', 'joined_at',
            'is_banned', 'ban_reason', 'banned_until', 'banned_by'
        ]
        read_only_fields = ['id', 'joined_at', 'banned_by']
    
    def get_user_details(self, obj):
        # Lazy import to avoid circular dependency
        from users.serializers import UserSerializer
        return UserSerializer(obj.user, context=self.context).data


class CommunityModeratorSerializer(serializers.ModelSerializer):
    """Serializer for the CommunityModerator model."""
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CommunityModerator
        fields = [
            'id', 'community', 'user', 'user_details',
            'appointed_at', 'appointed_by', 'permissions'
        ]
        read_only_fields = ['id', 'appointed_at']
    
    def get_user_details(self, obj):
        # Lazy import to avoid circular dependency
        from users.serializers import UserSerializer
        return UserSerializer(obj.user, context=self.context).data


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