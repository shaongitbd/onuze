from rest_framework import serializers
from users.serializers import UserBriefSerializer
from utils.sanitizers import sanitize_html
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model.
    """
    user = UserBriefSerializer(read_only=True)
    score = serializers.IntegerField(source='get_score', read_only=True)
    reply_count = serializers.IntegerField(source='get_reply_count', read_only=True)
    depth = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'user', 'parent', 'content', 'created_at', 
            'updated_at', 'is_edited', 'is_deleted', 'upvote_count', 
            'downvote_count', 'score', 'path', 'depth', 'reply_count'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at', 'is_edited', 
            'is_deleted', 'upvote_count', 'downvote_count', 'score', 
            'path', 'depth', 'reply_count'
        ]
    
    def validate_content(self, value):
        """
        Sanitize HTML content to prevent XSS attacks.
        """
        return sanitize_html(value)
    
    def create(self, validated_data):
        # Get the request from context
        request = self.context.get('request')
        
        # Set the user
        validated_data['user'] = request.user
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # If content was changed, use the edit method
        if 'content' in validated_data and validated_data['content'] != instance.content:
            instance.edit(validated_data['content'])
            return instance
        
        return super().update(instance, validated_data) 