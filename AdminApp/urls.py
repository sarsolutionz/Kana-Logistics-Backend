from django.urls import path
from AdminApp.views import UserSignUp, UserSignIn, UserProfile, ChangePassword, ResetPassword

urlpatterns = [
    path('SignUp/', UserSignUp.as_view(), name="SignUp"),
    path('SignIn/', UserSignIn.as_view(), name="SignIn"),
    path('profile/', UserProfile.as_view(), name="profile"),
    path('changepassword/', ChangePassword.as_view(), name="changepassword"),
    path('reset-password-email/', ResetPassword.as_view(), name="resetpassword"),
]
