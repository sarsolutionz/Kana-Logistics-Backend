from django.urls import path
from MemberApp.views import CreateVehicleAPI, GetAllVehicleInfoAPI, GetByIdVehicleInfo, UpdateVehicleInfoByID, \
    VehicleCapacityListView, CreateVehicleCapacityView, VehicleImageUploadView, UserVehicleImagesView, \
    DeleteImagesView

urlpatterns = [
    #
    # create vehicle
    path("create-vehicle", CreateVehicleAPI.as_view(), name="create-vehicle"),
    #
    # get all vehicle info
    path("all-vehicle-info", GetAllVehicleInfoAPI.as_view(),
         name="all-vehicle-info"),
    #
    # getById vehicle info
    path("vehicle", GetByIdVehicleInfo.as_view(), name="vehicle"),
    #
    # update vehicle info
    path("update-vehicle", UpdateVehicleInfoByID.as_view(), name="update-vehicle"),
    #
    # get all capacity
    path('capacities', VehicleCapacityListView.as_view(), name='vehicle-capacity-list'),
    #
    # create capacity
    path("create-capacity", CreateVehicleCapacityView.as_view(), name="create-vehicle"),
    # 
    # uplode image
    path('upload-images/', VehicleImageUploadView.as_view(), name='upload-images'),
    #
    # view all images according to
    path('vehicle/<int:user_id>/images/', UserVehicleImagesView.as_view(), name='user-vehicle-images'),
    #
    # delete images urls
    path('delete-images/<int:user_id>', DeleteImagesView.as_view(), name='delete-images'),
]
