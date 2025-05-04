from django.contrib import admin
from MemberApp.models import VehicleInfo, VehicleImage, DriverNotification

# Register your models here.

admin.site.register(VehicleInfo)

admin.site.register(VehicleImage)

admin.site.register(DriverNotification)
