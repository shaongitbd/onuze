from rest_framework import serializers
from users.serializers import UserBriefSerializer
from communities.serializers import CommunitySerializer
from .models import Report, BanAppeal


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer for Report model.
    """
    reporter = UserBriefSerializer(read_only=True)
    community = CommunitySerializer(read_only=True)
    resolved_by = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'community', 'content_type', 'content_id', 
            'reason', 'details', 'created_at', 'status', 'resolved_by', 
            'resolved_at', 'resolution_notes'
        ]
        read_only_fields = [
            'id', 'reporter', 'community', 'created_at', 'status', 
            'resolved_by', 'resolved_at', 'resolution_notes'
        ]
    
    def create(self, validated_data):
        # Set the reporter
        validated_data['reporter'] = self.context['request'].user
        
        # Determine community based on content (if possible)
        content_type = validated_data.get('content_type')
        content_id = validated_data.get('content_id')
        community = None
        
        if content_type == Report.POST:
            from posts.models import Post
            try:
                community = Post.objects.get(id=content_id).community
            except Post.DoesNotExist:
                raise serializers.ValidationError("Reported post not found.")
        elif content_type == Report.COMMENT:
            from comments.models import Comment
            try:
                community = Comment.objects.get(id=content_id).post.community
            except Comment.DoesNotExist:
                raise serializers.ValidationError("Reported comment not found.")
        elif content_type == Report.USER:
            # Reports against users are site-wide, no community link needed here
            # Or potentially link to a default/site-wide community if that concept exists
            pass
        
        if community:
            validated_data['community'] = community
        else:
            # Handle case where community cannot be determined (e.g., user report)
            # Maybe assign to a default site-wide mod queue or raise error?
            raise serializers.ValidationError("Could not determine community for this report.")
            
        return super().create(validated_data)


class BanAppealSerializer(serializers.ModelSerializer):
    """
    Serializer for BanAppeal model.
    """
    user = UserBriefSerializer(read_only=True)
    community = CommunitySerializer(read_only=True)
    reviewed_by = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = BanAppeal
        fields = [
            'id', 'user', 'appeal_type', 'community', 'reason', 'evidence',
            'status', 'created_at', 'reviewed_at', 'reviewed_by',
            'reviewer_notes', 'response_to_user', 'original_ban_reason',
            'original_banned_until'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'created_at', 'reviewed_at', 
            'reviewed_by', 'reviewer_notes', 'response_to_user'
        ]
    
    def create(self, validated_data):
        # Set the user making the appeal
        validated_data['user'] = self.context['request'].user
        
        # Populate ban details based on user's current ban status
        user = validated_data['user']
        appeal_type = validated_data.get('appeal_type')
        community_id = validated_data.get('community_id') # Assumes community_id is passed for community bans

        if appeal_type == BanAppeal.SITE_BAN:
            if user.is_banned:
                validated_data['original_ban_reason'] = user.site_ban_reason
                validated_data['original_banned_until'] = user.site_banned_until
            else:
                raise serializers.ValidationError("User is not currently site-banned.")
        elif appeal_type == BanAppeal.COMMUNITY_BAN:
            if community_id:
                from communities.models import CommunityMember, Community
                try:
                    community = Community.objects.get(id=community_id)
                    member = CommunityMember.objects.get(user=user, community=community)
                    if member.is_banned:
                        validated_data['community'] = community
                        validated_data['original_ban_reason'] = member.ban_reason
                        validated_data['original_banned_until'] = member.banned_until
                    else:
                        raise serializers.ValidationError("User is not currently banned from this community.")
                except (Community.DoesNotExist, CommunityMember.DoesNotExist):
                    raise serializers.ValidationError("Could not verify community ban status.")
            else:
                raise serializers.ValidationError("Community ID must be provided for community ban appeals.")
        
        return super().create(validated_data) 