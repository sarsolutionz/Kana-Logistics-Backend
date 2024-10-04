from rest_framework import serializers
from AdminApp.models import User

# Create your serializers here.


class UserSignUpSerializer(serializers.ModelSerializer):
    # We are writing this bcz we need confirm passwd field in our SignUp Request
    password2 = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ["email", "name", "password", "password2"]
        extra_kwargs = {'password': {'write_only': True}}

    # Validation of password & confirm password while UserSignUp
    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.get("password2")
        if password != password2:
            raise serializers.ValidationError({
                'auth_error': 'Passwords do not match. Please try again.'
            })

        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSignInSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        model = User
        fields = ["email", "password"]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "is_active", "is_admin"]


class UserChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=15, min_length=8, style={
                                     'input_type': 'password'}, write_only=True)
    password2 = serializers.CharField(max_length=15, min_length=8, style={
        'input_type': 'password'}, write_only=True)

    class Meta:
        fields = ["password", "password2"]

    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.get("password2")
        user = self.context.get("user")
        if password != password2:
            raise serializers.ValidationError({
                'auth_error': 'Passwords do not match. Please try again.'
            })
        user.set_password(password)
        user.save()
        return attrs
