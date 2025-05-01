from rest_framework import serializers
from .models import Vote
from posts.models import Post
from comments.models import Comment


class VoteSerializer(serializers.ModelSerializer):
    """
    Serializer for the Vote model.
    Handles validation and representation of votes.
    """
    user_id = serializers.UUIDField(read_only=True, source='user.id')
    username = serializers.CharField(read_only=True, source='user.username')
    
    class Meta:
        model = Vote
        fields = [
            'id', 'user_id', 'username', 'content_type', 'content_id',
            'vote_type', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'username', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """
        Create or update a vote according to the Vote model's custom method.
        """
        user = validated_data.get('user')
        content_type = validated_data.get('content_type')
        content_id = validated_data.get('content_id')
        vote_type = validated_data.get('vote_type')
        
        # Use the custom method to handle creation or update
        vote = Vote.create_or_update(
            user=user,
            content_type=content_type,
            content_id=content_id,
            vote_type=vote_type
        )
        
        # If the vote was toggled off (removed), return None
        if vote is None:
            raise serializers.ValidationError("Vote was removed (toggle behavior).")
            
        return vote
    
    def validate(self, data):
        """
        Validate that the content exists and the user can vote on it.
        """
        content_type = data.get('content_type')
        content_id = data.get('content_id')
        user = self.context['request'].user
        
        # Check if the content exists
        try:
            if content_type == Vote.POST:
                Post.objects.get(id=content_id)
            elif content_type == Vote.COMMENT:
                Comment.objects.get(id=content_id)
            else:
                raise serializers.ValidationError(f"Invalid content type: {content_type}")
        except (Post.DoesNotExist, Comment.DoesNotExist):
            raise serializers.ValidationError(f"{content_type.capitalize()} with id {content_id} does not exist.")
        
        # Check if the vote type is valid
        vote_type = data.get('vote_type')
        if vote_type not in [Vote.UPVOTE, Vote.DOWNVOTE]:
            raise serializers.ValidationError(f"Invalid vote type: {vote_type}")
        
        return data 