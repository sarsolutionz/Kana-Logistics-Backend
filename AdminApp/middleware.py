# middleware.py
from rest_framework_simplejwt.tokens import AccessToken
from .models import BlacklistedAccessToken
from django.http import JsonResponse

class AccessTokenBlacklistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token_str = auth_header.split(" ")[1]
            try:
                access_token = AccessToken(access_token_str)
                jti = access_token["jti"]

                # Check if the jti is blacklisted
                if BlacklistedAccessToken.objects.filter(jti=jti).exists():
                    return JsonResponse({"error": "Access token has been blacklisted."}, status=401)
            except Exception:
                return JsonResponse({"error": "Invalid access token."}, status=401)

        response = self.get_response(request)
        return response
