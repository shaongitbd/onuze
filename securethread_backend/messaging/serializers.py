from rest_framework import serializers
from users.serializers import UserBriefSerializer
from .models import PrivateMessage


class PrivateMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for PrivateMessage model.
    """
    sender = UserBriefSerializer(read_only=True)
    recipient = UserBriefSerializer(read_only=True)
    recipient_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = PrivateMessage
        fields = [
            'id', 'sender', 'recipient', 'recipient_id', 'subject', 'content', 
            'created_at', 'is_read', 'read_at'
        ]
        read_only_fields = [
            'id', 'sender', 'created_at', 'is_read', 'read_at'
        ]
    
    def create(self, validated_data):
        # Get the request from context
        request = self.context.get('request')
        
        # Set the sender
        validated_data['sender'] = request.user
        
        # Get recipient from ID
        from users.models import User
        recipient_id = validated_data.pop('recipient_id')
        try:
            recipient = User.objects.get(id=recipient_id)
            validated_data['recipient'] = recipient
        except User.DoesNotExist:
            raise serializers.ValidationError({"recipient_id": "Recipient user not found."})
        
        # Ensure user is not sending message to themselves
        if validated_data['sender'] == recipient:
            raise serializers.ValidationError("You cannot send a private message to yourself.")
            
        return super().create(validated_data) 