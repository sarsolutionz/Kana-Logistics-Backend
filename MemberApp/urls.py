from django.urls import path
from MemberApp.views import (
    CreateVehicleAPI,
    GetAllVehicleInfoAPI,
    GetByIdVehicleInfo,
    UpdateVehicleInfoByID,
    VehicleCapacityListView,
    CreateVehicleCapacityView,
    VehicleImageUploadView,
    UserVehicleImagesView,
    DeleteImagesView,
    VehicleNotificationAPIView,
    GetByIdVehicleNotification,
    LocationLockedNotifications,
    MarkNotificationRead,
    DeleteVehicleById,
    GetAllNotifications,
    GetReadNotifications,
    UpdateNotificationById,
    BulkDeleteNotifications,
    GetNotificationByIdView,
    RegisterFCMDeviceView,
    CreateDisplayPermissionsView,
    GetDisplayPermissionsView,
)

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
    #
    # get all capacity
    path("capacities", VehicleCapacityListView.as_view(), name="vehicle-capacity-list"),
    #
    # create capacity
    path("create-capacity", CreateVehicleCapacityView.as_view(), name="create-vehicle"),
    #
    # uplode image
    path("upload-images", VehicleImageUploadView.as_view(), name="upload-images"),
    #
    # view all images according to
    path("vehicle/images", UserVehicleImagesView.as_view(), name="user-vehicle-images"),
    #
    # delete images urls
    path("delete-images", DeleteImagesView.as_view(), name="delete-images"),
    #
    # create driver notifications
    path(
        "create-notifications/",
        VehicleNotificationAPIView.as_view(),
        name="create-notifications",
    ),
    # get all driver notifications
    path(
        "get-notifications/",
        GetByIdVehicleNotification.as_view(),
        name="get-notifications",
    ),
    #
    # locked notification
    path(
        "locked-notifications/",
        LocationLockedNotifications.as_view(),
        name="locked-notifications",
    ),
    #
    # Mark notification as read
    path(
        "notifications/mark-read/",
        MarkNotificationRead.as_view(),
        name="mark-notification-read",
    ),
    #
    # delete vehicle by id
    path("delete-vehicle", DeleteVehicleById.as_view(), name="delete-vehicle"),
    #
    # Get All Notifications
    path(
        "get-all-notifications",
        GetAllNotifications.as_view(),
        name="get-all-notifications",
    ),
    #
    # Get Read Notifications
    path(
        "get-read-notifications/",
        GetReadNotifications.as_view(),
        name="get-read-notifications",
    ),
    #
    # Get Notification By Id
    path(
        "update-notification",
        UpdateNotificationById.as_view(),
        name="update-notification-by-id",
    ),
    #
    # Bulk Delete Notifications
    path(
        "notifications/bulk-delete",
        BulkDeleteNotifications.as_view(),
        name="bulk-delete-notifications",
    ),
    #
    # Get Notification By Id
    path(
        "get-notification", GetNotificationByIdView.as_view(), name="get-notification"
    ),
    #
    # Register FCM
    path("register-fcm/", RegisterFCMDeviceView.as_view(), name="register-fcm"),
    #
    # Create Dislay Permission
    path(
        "create-display/", CreateDisplayPermissionsView.as_view(), name="create-display"
    ),
    #
    # Get Display Permissio
    path("get-display/", GetDisplayPermissionsView.as_view(), name="get-display"),
]
