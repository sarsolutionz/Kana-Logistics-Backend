from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from AuthApp.views import (
    SignUpAPI,
    SendOtpAPI,
    VerifyOtpAPI,
    ProfileDocsStatusAPI,
    UpdateLocationAPI,
    UserProfile,
    DeleteDriverAPI,
    GetAllDriverInfo,
    UpdateDriverById,
    GetDriverByIdView,
    DeleteDriverByIdAPI,
)

urlpatterns = [
    path("signup/<int:auth_type>/", SignUpAPI.as_view(), name="sign_up"),
    path("refresh-token/", TokenRefreshView.as_view(), name="token_refresh"),
    path("send-otp/", SendOtpAPI.as_view(), name="send_otp"),
    path("verify-otp/", VerifyOtpAPI.as_view(), name="verify_otp"),
    path("docs-status/", ProfileDocsStatusAPI.as_view(), name="docs_status"),
    path("update-location/", UpdateLocationAPI.as_view(), name="update_location"),
    path("user-profile/", UserProfile.as_view(), name="driver_profile"),
    path("delete-user", DeleteDriverAPI.as_view(), name="delete_user"),
    path("delete-partner", DeleteDriverByIdAPI.as_view(), name="delete-partner"),
    path("driver-info/", GetAllDriverInfo.as_view(), name="driver-info"),
    path('get-driver', GetDriverByIdView.as_view(), name='get-driver-by-id'),
    path("update-driver", UpdateDriverById.as_view(), name="update-driver"),
]
