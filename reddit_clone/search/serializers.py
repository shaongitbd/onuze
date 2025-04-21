from rest_framework import serializers
from users.serializers import UserBriefSerializer
from posts.serializers import PostSerializer
from comments.serializers import CommentSerializer
from communities.serializers import CommunitySerializer
from .models import SearchHistory


class SearchHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for search history.
    """
    user = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = SearchHistory
        fields = ['id', 'user', 'query', 'created_at', 'result_count']
        read_only_fields = ['id', 'user', 'created_at', 'result_count']


class SearchResultSerializer(serializers.Serializer):
    """
    Serializer for combined search results.
    """
    posts = PostSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    communities = CommunitySerializer(many=True, read_only=True)
    users = UserBriefSerializer(many=True, read_only=True)
    total_results = serializers.IntegerField(read_only=True)
    query = serializers.CharField(read_only=True) 