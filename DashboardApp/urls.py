from django.urls import path
from DashboardApp.views import DashboardAPIView

urlpatterns = [
    path("summary/", DashboardAPIView.as_view(), name="dashboard-view"),
]
