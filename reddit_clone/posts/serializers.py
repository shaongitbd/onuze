from rest_framework import serializers
from users.serializers import UserBriefSerializer
from communities.serializers import CommunitySerializer, FlairSerializer
from utils.sanitizers import sanitize_html
from .models import Post, PostMedia


class PostMediaSerializer(serializers.ModelSerializer):
    """
    Serializer for PostMedia model.
    """
    class Meta:
        model = PostMedia
        fields = ['id', 'post', 'media_type', 'media_url', 'thumbnail_url', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for Post model.
    """
    user = UserBriefSerializer(read_only=True)
    community = CommunitySerializer(read_only=True)
    community_id = serializers.UUIDField(write_only=True)
    flair = FlairSerializer(read_only=True)
    flair_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    media = PostMediaSerializer(many=True, read_only=True)
    score = serializers.IntegerField(source='get_score', read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'community', 'community_id', 'title', 'content', 
            'created_at', 'updated_at', 'is_edited', 'is_deleted', 'is_locked',
            'locked_reason', 'is_pinned', 'flair', 'flair_id', 'upvote_count',
            'downvote_count', 'comment_count', 'view_count', 'is_nsfw', 
            'is_spoiler', 'media', 'score'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at', 'is_edited', 'is_deleted',
            'is_locked', 'locked_reason', 'is_pinned', 'upvote_count', 
            'downvote_count', 'comment_count', 'view_count', 'media', 'score'
        ]
    
    def validate_content(self, value):
        """
        Sanitize HTML content to prevent XSS attacks.
        """
        return sanitize_html(value)
    
    def create(self, validated_data):
        # Get community_id and flair_id
        community_id = validated_data.pop('community_id')
        flair_id = validated_data.pop('flair_id', None)
        
        # Get the request from context
        request = self.context.get('request')
        
        # Create post
        from communities.models import Community, Flair
        
        try:
            community = Community.objects.get(id=community_id)
            
            if flair_id:
                try:
                    flair = Flair.objects.get(id=flair_id, community=community)
                    validated_data['flair'] = flair
                except Flair.DoesNotExist:
                    pass
            
            validated_data['community'] = community
            validated_data['user'] = request.user
            
            return super().create(validated_data)
            
        except Community.DoesNotExist:
            raise serializers.ValidationError({"community_id": "Community not found."})
    
    def update(self, instance, validated_data):
        # Handle flair_id
        flair_id = validated_data.pop('flair_id', None)
        
        if flair_id:
            from communities.models import Flair
            try:
                flair = Flair.objects.get(id=flair_id, community=instance.community)
                instance.flair = flair
            except Flair.DoesNotExist:
                pass
        
        # Update the post
        instance.title = validated_data.get('title', instance.title)
        
        # If content was changed, use the edit method
        if 'content' in validated_data and validated_data['content'] != instance.content:
            instance.edit(validated_data['content'])
        
        # Update other fields
        instance.is_nsfw = validated_data.get('is_nsfw', instance.is_nsfw)
        instance.is_spoiler = validated_data.get('is_spoiler', instance.is_spoiler)
        
        instance.save()
        return instance 