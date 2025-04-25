from rest_framework import serializers
from django.utils.timesince import timesince
from django.contrib.auth import get_user_model
from users.serializers import UserSerializer, UserBriefSerializer
from communities.models import Community, Flair
from communities.serializers import CommunitySerializer, FlairSerializer
from utils.sanitizers import sanitize_html
from .models import Post, PostMedia, Vote, PostImage, PostReport, PostSave

# Serializer for handling incoming media data during post creation
class IncomingPostMediaSerializer(serializers.Serializer):
    # Define choices directly within this serializer
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    media_url = serializers.URLField(required=True)
    media_type = serializers.ChoiceField(choices=MEDIA_TYPE_CHOICES, required=True)
    # Add other fields if needed, e.g., order, thumbnail_url (optional)
    thumbnail_url = serializers.URLField(required=False, allow_null=True)
    order = serializers.IntegerField(required=False, default=0)

    # We don't need Meta as it's not a ModelSerializer

# Serializer for displaying PostMedia (mostly read-only)
class PostMediaSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying PostMedia model data.
    """
    class Meta:
        model = PostMedia
        fields = ['id', 'post', 'media_type', 'media_url', 'thumbnail_url', 'order', 'created_at']
        read_only_fields = ['id', 'post', 'media_type', 'media_url', 'thumbnail_url', 'order', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for Post model. Handles nested media creation.
    """
    user = UserBriefSerializer(read_only=True)
    community = CommunitySerializer(read_only=True)
    community_path = serializers.CharField(source='community.path', read_only=True)
    community_id = serializers.UUIDField(write_only=True)
    flair = FlairSerializer(read_only=True)
    flair_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    # Read-only field to display existing media
    media_display = PostMediaSerializer(source='media', many=True, read_only=True) 
    score = serializers.IntegerField(source='get_score', read_only=True)
    
    # Writable field to accept media info during creation/update
    media = IncomingPostMediaSerializer(many=True, write_only=True, required=False)
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'community', 'community_path', 'community_id', 'title', 'path', 'content', 
            'created_at', 'updated_at', 'is_edited', 'is_deleted', 'is_locked',
            'locked_reason', 'is_pinned', 'flair', 'flair_id', 'upvote_count',
            'downvote_count', 'comment_count', 'view_count', 'is_nsfw', 
            'is_spoiler', 
            'media_display', # For reading existing media
            'media', # For writing/creating media links
            'score'
        ]
        read_only_fields = [
            'id', 'user', 'path', 'created_at', 'updated_at', 'is_edited', 'is_deleted',
            'is_locked', 'locked_reason', 'is_pinned', 'upvote_count', 
            'downvote_count', 'comment_count', 'view_count', 'media_display', 'score',
            'community_path'
        ]
    
    def validate(self, data):
        """
        Validate post data. Content OR media is required.
        """
        content = data.get('content')
        media_data = data.get('media')

        # On create (self.instance is None), require content OR media
        if not self.instance:
            has_content = content is not None and content.strip() != ''
            has_media = media_data is not None and len(media_data) > 0
            if not has_content and not has_media:
                raise serializers.ValidationError(
                    "Either content or media information is required to create a post."
                )
        # On update, specific logic might be needed if you allow removing all content/media
        # Handled by PostUpdateSerializer for now
        
        return data
    
    def validate_content(self, value):
        """
        Sanitize HTML content to prevent XSS attacks.
        """
        if value:
            return sanitize_html(value)
        return value
    
    def create(self, validated_data):
        # Separate media data from post data
        media_data = validated_data.pop('media', [])
        
        # Get community_id and flair_id
        community_id = validated_data.pop('community_id')
        flair_id = validated_data.pop('flair_id', None)
        
        # Get the request from context
        request = self.context.get('request')
        
        # Set community and user
        try:
            community = Community.objects.get(id=community_id)
            validated_data['community'] = community
        except Community.DoesNotExist:
            raise serializers.ValidationError({"community_id": "Community not found."})
            
        validated_data['user'] = request.user
        
        # Set flair if provided
        if flair_id:
            try:
                flair = Flair.objects.get(id=flair_id, community=community)
                validated_data['flair'] = flair
            except Flair.DoesNotExist:
                # Fail silently if flair doesn't exist or belong to community
                pass 
        
        # Create the Post instance first
        post = Post.objects.create(**validated_data)
        
        # Now create associated PostMedia instances
        for index, media_item in enumerate(media_data):
            PostMedia.objects.create(
                post=post,
                media_url=media_item['media_url'],
                media_type=media_item['media_type'],
                thumbnail_url=media_item.get('thumbnail_url'), # Optional
                order=media_item.get('order', index) # Use provided order or index
            )
            
        return post
    
    def update(self, instance, validated_data):
        # Handle media updates (more complex: delete old, add new?)
        # For now, let's simplify and assume media isn't updated via this main serializer
        # Pop media data to avoid trying to update it directly on the Post model
        validated_data.pop('media', None)
        
        # Handle flair_id update
        flair_id = validated_data.pop('flair_id', None)
        if flair_id:
            try:
                flair = Flair.objects.get(id=flair_id, community=instance.community)
                instance.flair = flair
            except Flair.DoesNotExist:
                instance.flair = None # Or handle error as needed
        elif 'flair_id' in self.initial_data and self.initial_data['flair_id'] is None:
             instance.flair = None # Allow removing flair
        
        # Update other post fields
        instance.title = validated_data.get('title', instance.title)
        instance.is_nsfw = validated_data.get('is_nsfw', instance.is_nsfw)
        instance.is_spoiler = validated_data.get('is_spoiler', instance.is_spoiler)
        
        # Check if content has changed
        content_changed = False
        content = None
        if 'content' in validated_data and validated_data['content'] != instance.content:
            content = validated_data['content']
            content_changed = True
        
        # If content changed, use the edit method, otherwise save normally
        if content_changed:
            instance.edit(content=content)
        else:
            # Save other potentially changed fields (flair, title, is_nsfw, is_spoiler)
            instance.save(update_fields=['flair', 'title', 'is_nsfw', 'is_spoiler'])
            
        return instance

# ... Keep other serializers like PostCreateSerializer, PostUpdateSerializer if needed ...
# ... Might need to adjust them or remove them depending on final usage ...

class PostCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating posts.
    (Potentially redundant now if PostSerializer handles creation well)
    """
    community_id = serializers.UUIDField(write_only=True)
    flair_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    media = IncomingPostMediaSerializer(many=True, write_only=True, required=False)
    
    class Meta:
        model = Post
        fields = [
            'community_id', 'title', 'content', 'flair_id',
            'is_nsfw', 'is_spoiler', 'media'
        ]
    
    def validate(self, data):
        content = data.get('content')
        media_data = data.get('media')
        has_content = content is not None and content.strip() != ''
        has_media = media_data is not None and len(media_data) > 0
        if not has_content and not has_media:
            raise serializers.ValidationError(
                "Either content or media information is required to create a post."
            )
        return data
    
    def validate_content(self, value):
        if value:
            return sanitize_html(value)
        return value

    def create(self, validated_data):
        media_data = validated_data.pop('media', [])
        community_id = validated_data.pop('community_id')
        flair_id = validated_data.pop('flair_id', None)
        request = self.context.get('request')
        
        try:
            community = Community.objects.get(id=community_id)
            validated_data['community'] = community
        except Community.DoesNotExist:
            raise serializers.ValidationError({"community_id": "Community not found."})
            
        validated_data['user'] = request.user
        
        if flair_id:
            try:
                flair = Flair.objects.get(id=flair_id, community=community)
                validated_data['flair'] = flair
            except Flair.DoesNotExist:
                pass
        
        post = Post.objects.create(**validated_data)
        
        for index, media_item in enumerate(media_data):
            PostMedia.objects.create(
                post=post,
                media_url=media_item['media_url'],
                media_type=media_item['media_type'],
                thumbnail_url=media_item.get('thumbnail_url'),
                order=media_item.get('order', index)
            )
            
        return post

# ... (PostUpdateSerializer might need similar adjustments if you allow media update) ...
# ... (Rest of the serializers: Vote, PostImage, PostReport, PostSave) ...

class PostUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating posts.
    """
    flair_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'flair_id', 'is_nsfw', 'is_spoiler']
    
    def validate(self, data):
        """
        Validate that we don't end up with no content and no media.
        """
        # Check if we're attempting to set content to empty
        if 'content' in data and (data['content'] is None or data['content'].strip() == ''):
            # Check if the instance has media
            instance = getattr(self, 'instance', None)
            if instance and not instance.media.exists():
                raise serializers.ValidationError("Either content or media attachments are required.")
        
        return data
    
    def validate_content(self, value):
        if value:
            return sanitize_html(value)
        return value


class VoteSerializer(serializers.ModelSerializer):
    """
    Serializer for post votes.
    """
    user = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = Vote
        fields = ['id', 'post', 'user', 'vote_type', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class PostImageSerializer(serializers.ModelSerializer):
    """
    Serializer for post images.
    """
    class Meta:
        model = PostImage
        fields = ['id', 'post', 'image_url', 'order', 'created_at']
        read_only_fields = ['id', 'created_at'] 


class PostReportSerializer(serializers.ModelSerializer):
    """
    Serializer for post reports.
    """
    user = UserBriefSerializer(read_only=True)
    post_title = serializers.SerializerMethodField(read_only=True)
    resolved_by_details = UserBriefSerializer(source='resolved_by', read_only=True)
    
    class Meta:
        model = PostReport
        fields = [
            'id', 'post', 'post_title', 'user', 'reason', 'description', 
            'created_at', 'resolved', 'resolved_by', 'resolved_by_details', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'resolved', 'resolved_by', 
            'resolved_by_details', 'resolved_at', 'post_title'
        ]
    
    def get_post_title(self, obj):
        return obj.post.title if obj.post else None
    
    def create(self, validated_data):
        # Get the user from the request
        request = self.context.get('request')
        validated_data['user'] = request.user
        
        # Create the report
        return super().create(validated_data)


class PostSaveSerializer(serializers.ModelSerializer):
    """
    Serializer for saved posts.
    """
    user = UserBriefSerializer(read_only=True)
    post_details = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = PostSave
        fields = ['id', 'post', 'post_details', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at', 'post_details']
    
    def get_post_details(self, obj):
        # Return minimal post details to avoid circular references
        if not obj.post:
            return None
        return {
            'id': obj.post.id,
            'title': obj.post.title,
            'path': obj.post.path,
            'community_name': obj.post.community.name if obj.post.community else None,
            'community_path': obj.post.community.path if obj.post.community else None,
        }
    
    def create(self, validated_data):
        # Get the user from the request
        request = self.context.get('request')
        validated_data['user'] = request.user
        
        # Create the saved post entry
        return super().create(validated_data) 