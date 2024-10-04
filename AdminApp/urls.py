from django.urls import path
from AdminApp.views import UserSignUp, UserSignIn, UserProfileView

urlpatterns = [
    path('SignUp/', UserSignUp.as_view(), name="SignUp"),
    path('SignIn/', UserSignIn.as_view(), name="SignIn"),
    path('profile/', UserProfileView.as_view(), name="profile"),
]
