from django.contrib import admin
from MemberApp.models import VehicleInfo, VehicleImage, DriverNotification, UserFCMDevice, Display

# Register your models here.

admin.site.register(VehicleInfo)

admin.site.register(VehicleImage)

admin.site.register(DriverNotification)

admin.site.register(UserFCMDevice)

admin.site.register(Display)