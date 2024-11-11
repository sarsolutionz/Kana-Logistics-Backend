from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from django.contrib.auth import authenticate

from AdminApp.renderers import UserRenderer
from AdminApp.serializers import SignUpSerializer, SignInSerializer, ProfileSerializer, ChangePasswordSerializer, PasswordResetEmailSerializer, PasswordResetSerializer

from .models import BlacklistedAccessToken

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
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = get_tokens_for_user(user=user)
        return Response({"token": token, "msg": "User SignUp Successfully"}, status=status.HTTP_201_CREATED)


class UserSignIn(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        serializer = SignInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.data.get("email")
        password = serializer.data.get("password")
        user = authenticate(email=email, password=password)
        if user is not None and user.is_active:
            token = get_tokens_for_user(user=user)
            return Response({"user": user.is_authenticated, "email": user.email, "token": token, "msg": "User SignIn Successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"errors": {"non_field_errors": ["Email or Password is not valid"]}}, status=status.HTTP_404_NOT_FOUND)


class UserProfile(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePassword(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        return Response({"msg": "Password Changed Successfully"}, status=status.HTTP_200_OK)


class PasswordResetEmail(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        serializer = PasswordResetEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"msg": "Password Reset link send. Please check your Email"}, status=status.HTTP_200_OK)


class PasswordReset(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, uid, token, format=None):
        serializer = PasswordResetSerializer(data=request.data, context={
                                             "uid": uid, "token": token})
        serializer.is_valid(raise_exception=True)
        return Response({"msg": "Password Reset Successfully"}, status=status.HTTP_200_OK)


class UserLogout(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Extract the access token from the Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return Response({"error": "Access token is required."}, status=status.HTTP_400_BAD_REQUEST)

            access_token_str = auth_header.split(" ")[1]
            access_token = AccessToken(access_token_str)

            # Blacklist the access token by its jti
            BlacklistedAccessToken.objects.create(jti=access_token["jti"])

            return Response({"msg": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
