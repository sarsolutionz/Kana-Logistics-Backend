from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from AuthApp.views import (
    SignUpAPI,
    SendOtpAPI,
    VerifyOtpAPI,
    ProfileDocsStatusAPI,
    UpdateLocationAPI,
    UserProfile
)

urlpatterns = [
    path("signup/<int:auth_type>/", SignUpAPI.as_view(), name="sign_up"),
    path("refresh-token/", TokenRefreshView.as_view(), name="token_refresh"),
    path("send-otp/", SendOtpAPI.as_view(), name="send_otp"),
    path("verify-otp/", VerifyOtpAPI.as_view(), name="verify_otp"),
    path("docs-status/", ProfileDocsStatusAPI.as_view(), name="docs_status"),
    path("update-location/", UpdateLocationAPI.as_view(), name="update_location"),
    path("user-profile/", UserProfile.as_view(), name="driver_profile"),
]
