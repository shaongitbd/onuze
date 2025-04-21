from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Role, UserBlock

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    """
    Simplified version of User serializer for embedding in other models.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'karma']
        read_only_fields = ['id', 'username', 'avatar', 'karma']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'date_joined', 'last_login',
            'bio', 'avatar', 'karma', 'is_verified', 'is_staff',
            'two_factor_enabled'
        ]
        read_only_fields = [
            'id', 'email', 'date_joined', 'last_login', 'karma',
            'is_verified', 'is_staff'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirmation = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirmation',
            'bio', 'avatar'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirmation'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            bio=validated_data.get('bio', ''),
            avatar=validated_data.get('avatar', '')
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profiles.
    """
    class Meta:
        model = User
        fields = ['username', 'bio', 'avatar', 'two_factor_enabled']
        

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    """
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for Role model.
    """
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']


class UserBlockSerializer(serializers.ModelSerializer):
    """
    Serializer for UserBlock model.
    """
    blocked_user = UserBriefSerializer(read_only=True)
    blocked_user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = UserBlock
        fields = ['id', 'user', 'blocked_user', 'blocked_user_id', 'created_at', 'reason']
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        # Set the current user as the blocking user
        validated_data['user'] = self.context['request'].user
        
        # Get the blocked user from the provided ID
        blocked_user_id = validated_data.pop('blocked_user_id')
        try:
            blocked_user = User.objects.get(id=blocked_user_id)
            validated_data['blocked_user'] = blocked_user
        except User.DoesNotExist:
            raise serializers.ValidationError({"blocked_user_id": "User not found."})
        
        # Check if trying to block self
        if validated_data['user'] == blocked_user:
            raise serializers.ValidationError({"blocked_user_id": "You cannot block yourself."})
        
        return super().create(validated_data) 