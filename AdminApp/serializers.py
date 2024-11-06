from AdminApp.models import User
from rest_framework import serializers

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_str, force_bytes, DjangoUnicodeDecodeError

from AdminApp.utils import Util

# Create your serializers here.


class SignUpSerializer(serializers.ModelSerializer):
    # We are writing this bcz we need confirm passwd field in our SignUp Request
    password2 = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ["email", "name", "password", "password2"]
        extra_kwargs = {'password': {'write_only': True}}

    # Validation of password & confirm password while SignUp
    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.get("password2")
        if password != password2:
            raise serializers.ValidationError({
                'email': 'Passwords do not match. Please try again.'
            })

        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class SignInSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        model = User
        fields = ["email", "password"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "is_active", "is_admin"]


class ChangePasswordSerializer(serializers.Serializer):
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


class PasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        fields = ["email"]

    def validate(self, attrs):
        email = attrs.get("email")
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            link = "http://127.0.0.1:8000/api/user/reset/"+ uid + "/" + token
            data = {
                "subject": "Reset Your Password",
                "body": "Click Following Link to Reset Your Password: " + link,
                "to_email": user.email
            }
            Util.send_email(data=data)            
            return attrs
        else:
            raise serializers.ValidationError({"User": "Invalid credentials."})

class PasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=15, min_length=8, style={
                                     'input_type': 'password'}, write_only=True)
    password2 = serializers.CharField(max_length=15, min_length=8, style={
        'input_type': 'password'}, write_only=True)

    class Meta:
        fields = ["password", "password2"]

    def validate(self, attrs):
        try:
            password = attrs.get("password")
            password2 = attrs.get("password2")
            uid = self.context.get("uid")
            token = self.context.get("token")
            if password != password2:
                raise serializers.ValidationError({
                    'auth_error': 'Passwords do not match. Please try again.'
                })
            id = smart_str(urlsafe_base64_decode(uid))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user=user, token=token):
                raise serializers.ValidationError({"Token": "Invalid token or Expired."})
            user.set_password(password)
            user.save()
            return attrs
        except DjangoUnicodeDecodeError as identifier:
            PasswordResetTokenGenerator().check_token(user=user, token=token)
            raise serializers.ValidationError({"Token": "Invalid token or Expired."})