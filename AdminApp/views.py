from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate

from AdminApp.renderers import UserRenderer
from AdminApp.serializers import UserSignUpSerializer, UserSignInSerializer, UserProfileSerializer, UserChangePasswordSerializer

# Creating tokens manually


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# Create your views here.


class UserSignUp(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        serializer = UserSignUpSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            token = get_tokens_for_user(user=user)
            return Response({"token": token, "msg": "User SignUp Successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSignIn(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        serializer = UserSignInSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.data.get("email")
            password = serializer.data.get("password")
            user = authenticate(email=email, password=password)
            if user is not None and user.is_admin:
                token = get_tokens_for_user(user=user)
                return Response({"token": token, "msg": "User SignIn Successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"errors": {"non_field_errors": ["Email or Password is not valid"]}}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfile(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePassword(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = UserChangePasswordSerializer(
            data=request.data, context={"user": request.user})
        if serializer.is_valid(raise_exception=True):
            return Response({"msg": "Password Changed Successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
