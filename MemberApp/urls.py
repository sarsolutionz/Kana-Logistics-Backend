from django.urls import path
from MemberApp.views import CreateVehicleAPI, GetAllVehicleInfoAPI, GetByIdVehicleInfo, UpdateVehicleInfoByID

urlpatterns = [
    #
    # create vehicle 
    path("create-vehicle", CreateVehicleAPI.as_view(), name="create-vehicle"),
    #
    # get all vehicle info
    path("all-vehicle-info", GetAllVehicleInfoAPI.as_view(), name="all-vehicle-info"),
    #
    # getById vehicle info
    path("vehicle", GetByIdVehicleInfo.as_view(), name="vehicle"),
    #
    # update vehicle info
    path("update-vehicle", UpdateVehicleInfoByID.as_view(), name="update-vehicle"),
]
