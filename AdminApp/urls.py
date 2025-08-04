from django.urls import path
from AdminApp.views import UserSignUp, UserSignIn, UserProfile, GetAllProfiles, ChangePassword, PasswordResetEmail, PasswordReset, UserLogout, EditUserById, GetUserByIdView, EditProfileById, TokenRefreshView

urlpatterns = [
    path('SignUp', UserSignUp.as_view(), name="SignUp"),
    path('SignIn', UserSignIn.as_view(), name="SignIn"),
    path('logout', UserLogout.as_view(), name="logout"),
    path('profile', UserProfile.as_view(), name="profile"),
    path('get-all-profiles', GetAllProfiles.as_view(), name="profiles"),
    path('profile-edit', EditProfileById.as_view(), name="profile-edit"),
    path('user-edit', EditUserById.as_view(), name='user-edit'),
    path('get-user', GetUserByIdView.as_view(), name='get-user-by-id'),
    path('changepassword/', ChangePassword.as_view(), name="changepassword"),
    path('reset-password-email/', PasswordResetEmail.as_view(), name="resetpassword"),
    path('reset-password/<uid>/<token>/', PasswordReset.as_view(), name="resetpassword"),
    path('token/check-refresh/', TokenRefreshView.as_view(), name='token_check_refresh'),
]
