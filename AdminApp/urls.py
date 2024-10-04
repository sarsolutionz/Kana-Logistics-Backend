from django.urls import path
from AdminApp.views import UserSignUp, UserSignIn

urlpatterns = [
    path('SignUp/', UserSignUp.as_view(), name="SignUp"),
    path('SignIn/', UserSignIn.as_view(), name="SignIn"),
]
