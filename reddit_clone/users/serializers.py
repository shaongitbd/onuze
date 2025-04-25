from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
import re
import logging
import requests
from django.conf import settings
from .models import Role, UserBlock
from captcha.fields import CaptchaField

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
    communities = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'date_joined', 'last_login',
            'bio', 'avatar', 'karma', 'is_verified', 'is_staff',
            'two_factor_enabled', 'communities'
        ]
        read_only_fields = [
            'id', 'email', 'date_joined', 'last_login', 'karma',
            'is_verified', 'is_staff', 'communities'
        ]
    
    def get_communities(self, obj):
        # Lazy import to avoid circular dependency
        from communities.serializers import CommunityBriefSerializer
        # Get the communities this user is a member of
        communities = obj.communities.filter(is_approved=True).values_list('community', flat=True)
        from communities.models import Community
        communities = Community.objects.filter(id__in=communities)
        return CommunityBriefSerializer(communities, many=True, context=self.context).data


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirmation = serializers.CharField(write_only=True, required=True)
    captcha = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirmation',
            'bio', 'avatar', 'captcha'
        ]
    
    def validate_username(self, value):
        """
        Check that the username meets requirements and is unique.
        """
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        
        # Check if username contains only allowed characters
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, underscores, and hyphens.")
            
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirmation'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate CAPTCHA
        captcha_token = attrs.pop('captcha')
        self.validate_captcha(captcha_token)
        
        return attrs
    
    def validate_captcha(self, value):
        """
        Validate the CAPTCHA token with the server.
        """
        # from django.conf import settings
        # import requests
        
        # Check if CAPTCHA validation is enabled
        if not getattr(settings, 'CAPTCHA_ENABLED', True):
            return True
            
        # For Django Simple Captcha
        if getattr(settings, 'SIMPLE_CAPTCHA_ENABLED', False):
            # from captcha.fields import CaptchaField
            try:
                captcha_field = CaptchaField()
                captcha_field.clean(value)
                return True
            except Exception as e:
                raise serializers.ValidationError(f"Invalid CAPTCHA: {str(e)}")
        
        # For reCAPTCHA
        elif getattr(settings, 'RECAPTCHA_ENABLED', False):
            recaptcha_secret = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
            if not recaptcha_secret:
                # Log warning but allow registration without verification if not configured
                # import logging
                logger = logging.getLogger(__name__)
                logger.warning("reCAPTCHA is enabled but secret key is not configured")
                return True
                
            try:
                # Verify with reCAPTCHA API
                response = requests.post(
                    'https://www.google.com/recaptcha/api/siteverify',
                    data={
                        'secret': recaptcha_secret,
                        'response': value
                    }
                )
                result = response.json()
                
                if not result.get('success', False):
                    error_codes = result.get('error-codes', [])
                    raise serializers.ValidationError(f"CAPTCHA verification failed: {', '.join(error_codes)}")
                
                return True
            except Exception as e:
                if isinstance(e, serializers.ValidationError):
                    raise
                raise serializers.ValidationError(f"CAPTCHA verification error: {str(e)}")
        
        return True
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            bio=validated_data.get('bio', ''),
            avatar=validated_data.get('avatar', '')
        )
        
        # Send welcome notification
        from notifications.models import Notification
        try:
            Notification.send_welcome_notification(user)
        except Exception as e:
            # Log the error but continue with user creation
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send welcome notification: {str(e)}")
            
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
    # Make user read-only in the Meta fields but set the default here
    user = serializers.PrimaryKeyRelatedField(
        read_only=True, 
        default=serializers.CurrentUserDefault()
    )
    blocked_user = UserBriefSerializer(read_only=True)
    blocked_user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = UserBlock
        # Ensure 'user' is listed here but it will be handled by CurrentUserDefault
        fields = ['id', 'user', 'blocked_user', 'blocked_user_id', 'created_at', 'reason']
        # 'user' is effectively read-only from the perspective of input data,
        # but will be populated by CurrentUserDefault on creation.
        read_only_fields = ['id', 'created_at', 'blocked_user'] # Removed 'user' from here
    
    # Remove the explicit setting of user in create method
    def create(self, validated_data):
        # user is now automatically set by CurrentUserDefault
        
        # Get the blocked user from the provided ID
        blocked_user_id = validated_data.pop('blocked_user_id')
        try:
            blocked_user = User.objects.get(id=blocked_user_id)
            validated_data['blocked_user'] = blocked_user
        except User.DoesNotExist:
            raise serializers.ValidationError({"blocked_user_id": "User not found."})
        
        # Check if trying to block self
        # Need to get the user from the validated_data or default context now
        requesting_user = self.context['request'].user
        if requesting_user == blocked_user:
            raise serializers.ValidationError({"blocked_user_id": "You cannot block yourself."})
        
        # Ensure the user field is correctly populated before calling super()
        # CurrentUserDefault should handle this, but explicit check can be added if needed
        # validated_data['user'] = requesting_user # Usually not needed if CurrentUserDefault works
        
        return super().create(validated_data) 