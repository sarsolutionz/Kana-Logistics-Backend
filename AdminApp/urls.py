from django.urls import path
from AdminApp.views import UserSignUp, UserSignIn, UserProfile, GetAllProfiles, ChangePassword, PasswordResetEmail, PasswordReset, UserLogout, EditUserById, GetUserByIdView

urlpatterns = [
    path('SignUp', UserSignUp.as_view(), name="SignUp"),
    path('SignIn', UserSignIn.as_view(), name="SignIn"),
    path('logout', UserLogout.as_view(), name="logout"),
    path('profile', UserProfile.as_view(), name="profile"),
    path('get-all-profiles', GetAllProfiles.as_view(), name="profiles"),
    path('user-edit', EditUserById.as_view(), name='user-edit'),
    path('get-user', GetUserByIdView.as_view(), name='get-user-by-id'),
    path('changepassword/', ChangePassword.as_view(), name="changepassword"),
    path('reset-password-email/', PasswordResetEmail.as_view(), name="resetpassword"),
    path('reset-password/<uid>/<token>/', PasswordReset.as_view(), name="resetpassword"),
]
