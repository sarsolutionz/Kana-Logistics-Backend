from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from AuthApp.views import (
    SignUpAPI,
)

urlpatterns = [
    path("signup/<int:auth_type>/", SignUpAPI.as_view(), name="sign_up"),
    path("refresh-token/", TokenRefreshView.as_view(), name="token_refresh"),
]
