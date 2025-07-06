from AdminApp.models import User
from rest_framework import serializers

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_str, force_bytes, DjangoUnicodeDecodeError

from AdminApp.utils import Util

import re

# Create your serializers here.


class SignUpSerializer(serializers.ModelSerializer):
    # We are writing this bcz we need confirm passwd field in our SignUp Request
    password2 = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)
    number = serializers.CharField(
        write_only=True, max_length=10, min_length=10)

    class Meta:
        model = User
        fields = ["email", "name", "password", "password2", "number"]
        extra_kwargs = {'password': {'write_only': True}}

    # Validation of password & confirm password while SignUp
    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.get("password2")
        number = attrs.get("number")
        if password != password2:
            raise serializers.ValidationError({
                'email': 'Passwords do not match. Please try again.'
            })
        
        if not re.match(r'^\d{10}$', number):
            raise serializers.ValidationError({
                'number': 'Enter a valid 10-digit phone number.'
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
        fields = ["id", "email", "name", "number", "is_active", "is_admin", "is_blocked"]


class GetAllProfilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "number",
                  "is_active", "is_admin", "is_blocked", "role"]


class UserEditByIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'is_active', 'number',
                  'role', 'is_admin', 'is_blocked']
        extra_kwargs = {
            # 'email': {'read_only': True},
            'id': {'read_only': True},
            # Prevent direct admin status changes
            'is_admin': {'read_only': True}
        }

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value.lower() if value else value

    def validate(self, data):
        requesting_user = self.context['request'].user
        target_user = self.instance

        # Check if role is being changed
        if 'role' in data:
            # Admin can set any role (including admin) for any user
            if not requesting_user.is_admin:
                raise serializers.ValidationError(
                    {"role": "Only admin users can change roles."}
                )

            # Additional check if trying to set admin role
            if data['role'] == 'admin' and not requesting_user.is_admin:
                raise serializers.ValidationError(
                    {"role": "Only superusers can assign admin role."}
                )
            
        # is_active change restriction
        if 'is_active' in data:
            if getattr(target_user, 'is_admin', False) and getattr(target_user, 'role', '') == 'admin':
                raise serializers.ValidationError({
                    "is_active": "Cannot update active status for admin users."
                })
            
        if 'role' in data:
            if getattr(target_user, 'is_admin', True) and getattr(target_user, 'role', '') == 'admin':
                raise serializers.ValidationError({
                    "role": "Cannot update role status for admin users."
                })

        return data

    def update(self, instance, validated_data):
        requesting_user = self.context['request'].user

        # Auto-set is_admin based on role
        if 'role' in validated_data:
            new_role = validated_data['role']
            validated_data['is_admin'] = (new_role == 'admin')

            # If promoting to admin, ensure the requesting user is superuser
            if new_role == 'admin' and not requesting_user.is_admin:
                raise serializers.ValidationError(
                    {"role": "Only superusers can create admin users."}
                )

        # Admin can activate/deactivate users
        if 'is_active' in validated_data and not requesting_user.is_admin:
            raise serializers.ValidationError(
                {"is_active": "Only admin users can change activation status."}
            )

        return super().update(instance, validated_data)


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'number', 'is_active',
                  'role', 'is_admin', 'is_blocked', 'created_at', 'updated_at']
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=15, min_length=8, style={
                                     'input_type': 'password'}, write_only=True)
    confirm = serializers.CharField(max_length=15, min_length=8, style={
        'input_type': 'password'}, write_only=True)
    
    current = serializers.CharField(max_length=15, min_length=8, style={
        'input_type': 'password'}, write_only=True)

    class Meta:
        fields = ["password", "confirm", "current"]

    def validate(self, attrs):
        current = attrs.get("current")
        password = attrs.get("password")
        confirm = attrs.get("confirm")
        user = self.context.get("user")
        if not user.check_password(current):
            raise serializers.ValidationError({
                'auth_error': 'Current password is incorrect.'
            })
        if password != confirm:
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
            link = "http://127.0.0.1:8000/api/user/reset/" + uid + "/" + token
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
                raise serializers.ValidationError(
                    {"Token": "Invalid token or Expired."})
            user.set_password(password)
            user.save()
            return attrs
        except DjangoUnicodeDecodeError as identifier:
            PasswordResetTokenGenerator().check_token(user=user, token=token)
            raise serializers.ValidationError(
                {"Token": "Invalid token or Expired."})
