"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_title = "Kana Logistics"
admin.site.site_header = "Kana Logistics SuperAdmin"
admin.site.index_title = "Kana Logistics"

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('api/user/', include('AdminApp.urls')),
    path('api/member/', include('MemberApp.urls')),
    path('api/mobile-auth/', include('AuthApp.urls')),
    path('api/dashboard/', include('DashboardApp.urls')),
]

# Add the following lines to the bottom of the file

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)