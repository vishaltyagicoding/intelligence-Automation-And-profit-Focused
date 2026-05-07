"""
User Serializers
================
Serializers for user authentication and profile
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with comprehensive validation"""
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        max_length=128,
        min_length=8
    )
    password2 = serializers.CharField(write_only=True, required=True, max_length=128)
    email = serializers.EmailField(required=True, max_length=254)
    username = serializers.CharField(required=True, max_length=150, min_length=3)
    first_name = serializers.CharField(required=True, max_length=150, min_length=1)
    last_name = serializers.CharField(required=True, max_length=150, min_length=1)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        """Validate email field"""
        if not value or not value.strip():
            raise serializers.ValidationError("Email address is required.")
        
        value = value.strip().lower()
        
        if len(value) > 254:
            raise serializers.ValidationError("Email address is too long (max 254 characters).")
        
        # Check if email already exists
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return value
    
    def validate_username(self, value):
        """Validate username field"""
        if not value or not value.strip():
            raise serializers.ValidationError("Username is required.")
        
        value = value.strip()
        
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        
        if len(value) > 150:
            raise serializers.ValidationError("Username is too long (max 150 characters).")
        
        # Check if username already exists
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        return value
    
    def validate_first_name(self, value):
        """Validate first name field"""
        if not value or not value.strip():
            raise serializers.ValidationError("First name is required.")
        if len(value.strip()) > 150:
            raise serializers.ValidationError("First name is too long (max 150 characters).")
        if len(value.strip()) < 1:
            raise serializers.ValidationError("First name cannot be empty.")
        return value.strip()
    
    def validate_last_name(self, value):
        """Validate last name field"""
        if not value or not value.strip():
            raise serializers.ValidationError("Last name is required.")
        if len(value.strip()) > 150:
            raise serializers.ValidationError("Last name is too long (max 150 characters).")
        if len(value.strip()) < 1:
            raise serializers.ValidationError("Last name cannot be empty.")
        return value.strip()
    
    def validate(self, attrs):
        """Cross-field validation"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """Create user with validated data"""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    full_name = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone', 'avatar', 'bio', 'is_active',
            'is_verified', 'email_verified', 'created_at', 'subscription_status', 
            'manual_subscription', 'trial_status'
        ]
        read_only_fields = ['id', 'email', 'is_active', 'is_verified', 'created_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_subscription_status(self, obj):
        try:
            subscription = obj.subscription
            from django.utils import timezone
            
            # Calculate precise time remaining
            trial_end_iso = None
            days_remaining = 0
            hours_remaining = 0
            minutes_remaining = 0
            
            if subscription.status == 'trial' and subscription.trial_end:
                trial_end_iso = subscription.trial_end.isoformat()
                time_left = subscription.trial_end - timezone.now()
                if time_left.total_seconds() > 0:
                    days_remaining = time_left.days
                    hours_remaining = (time_left.seconds // 3600)
                    minutes_remaining = (time_left.seconds % 3600) // 60
            elif subscription.status == 'active' and subscription.end_date:
                trial_end_iso = subscription.end_date.isoformat()
            
            return {
                'plan': subscription.plan,
                'status': subscription.status,
                'is_active': subscription.is_active(),
                'days_remaining': subscription.days_remaining(),
                'trial_end': trial_end_iso,  # ISO format for precise countdown
                'hours_remaining': hours_remaining,
                'minutes_remaining': minutes_remaining,
                'trial_status': obj.trial_status,  # Include trial_status from User model
            }
        except:
            return None


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with user data"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user data to response
        data['user'] = UserSerializer(self.user).data
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
