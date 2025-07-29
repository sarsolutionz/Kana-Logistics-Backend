from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser

from AdminApp.renderers import UserRenderer

from django.db import IntegrityError
from datetime import datetime

from MemberApp.models import VehicleInfo, VehicleImage, DriverNotification, UserFCMDevice, Display, RolePermissionConfig

from services.notification_service import send_push_notification
from django.db.models import Q
from django.contrib.auth import get_user_model
User = get_user_model()

from uuid import UUID
import uuid

from MemberApp.serializers import CreateVehicleInfoSerializer, GetAllVehicleInfoSerializer, \
    GetByIdVehicleInfoSerializer, UpdateVehicleInfoByIDSerializer, VehicleCapacitySerializer, \
    CreateVehicleCapacitySerializer, CreateDocumentSerializer, DeleteDocumentSerializer, \
    VehicleImageSerializer, VehicleNotificationCreateSerializer, BulkVehicleNotificationSerializer, GetVehicleNotificationByIdSerializer, NotificationDetailSerializer, NotificationReadSerializer, \
    ReadNotificationSerializer, UpdateNotificationByIdSerializer, UserBasicSerializer

import logging

logger = logging.getLogger(__name__)


# Create your views here.

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "admin"

class CreateVehicleAPI(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CreateVehicleInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle_info = serializer.save()
        vehicle_id = str(vehicle_info.id) if isinstance(vehicle_info.id, UUID) else vehicle_info.id
        return Response({"message": "Vehicle information created successfully", "vehicle_id": vehicle_id}, status=status.HTTP_201_CREATED)


class GetAllVehicleInfoAPI(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            vehicles = VehicleInfo.objects.all().order_by('id')
            for vehicle in vehicles:
                vehicle.update_status()
            serializer = GetAllVehicleInfoSerializer(vehicles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetByIdVehicleInfo(RetrieveAPIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            vehicle_id = request.query_params.get('vehicle_id', None)
            vehicle = VehicleInfo.objects.get(id=vehicle_id)
            serializer = GetByIdVehicleInfoSerializer(vehicle)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except VehicleInfo.DoesNotExist:
            return Response({"error": "Vehicle not found"}, status=404)


class UpdateVehicleInfoByID(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        try:
            vehicle_id = request.query_params.get('vehicle_id', None)
            vehicle = VehicleInfo.objects.get(id=vehicle_id)
            serializer = UpdateVehicleInfoByIDSerializer(
                vehicle, data=request.data, partial=False)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except VehicleInfo.DoesNotExist:
            return Response({"error": "Vehicle not found"}, status=404)


class VehicleCapacityListView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            capacities = VehicleInfo.objects.all()
            for vehicle in capacities:
                vehicle.update_status()
            serializer = VehicleCapacitySerializer(capacities, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
            return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateVehicleCapacityView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CreateVehicleCapacitySerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Save the new capacity instance
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({"error": "Capacity already exists."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# New API View for uploading multiple VehicleImage instances
class VehicleImageUploadView(APIView):
    """API View for uploading multiple VehicleImage instances."""
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    # Ensure multipart parser is used
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        serializer = CreateDocumentSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Images uploaded successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API for get all images uploaded earlier
class UserVehicleImagesView(APIView):
    """API View to retrieve all VehicleImage instances for a specific user."""
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Filter images by user_id (assuming a relationship exists between Vehicle and User)
        user_id = request.query_params.get('user_id', None)
        images = VehicleImage.objects.filter(vehicle_id=user_id)

        if not images.exists():
            return Response(
                {"message": "No images found for the specified user."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = VehicleImageSerializer(images, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# API for delete single and multiple images at a time
class DeleteImagesView(APIView):
    """API View to delete multiple VehicleImage instances along with their media files."""
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, *args, **kwargs):
        serializer = DeleteDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = request.query_params.get('user_id', None)
        deleted_count, errors = serializer.delete_images(user_id)

        response_data = {
            "message": f"{deleted_count} images were successfully deleted."}
        if errors:
            response_data["errors"] = errors

        return Response(response_data, status=status.HTTP_200_OK)

class VehicleNotificationAPIView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'vehicle_ids' in request.data and 'notifications' in request.data:
            return self.handle_bulk_create(request)
        return self.handle_single_create(request)

    def handle_single_create(self, request):
        response = {"status": 400}
        serializer = VehicleNotificationCreateSerializer(data=request.data)
        if serializer.is_valid():
            vehicle_id = serializer.validated_data.pop('vehicle_id')
            vehicle = VehicleInfo.objects.get(id=vehicle_id)
            user = User.objects.filter(number=vehicle.alternate_number).first()
            if user:
                user = user.id
            else:
                response["status"] = 400
                response["message"] = "User not found"

            notification = DriverNotification.objects.create(
                vehicle=vehicle,
                created_by=request.user,
                **serializer.validated_data
            )

            # Send push notification with all details
            notification_data = {
                "notification_id": str(notification.id),
                "vehicle_id": str(vehicle_id),
                "source": notification.source,
                "destination": notification.destination,
                "rate": str(notification.rate),
                "weight": str(notification.weight),
                "date": str(notification.date) if notification.date else None,
                "message": notification.message,
                "contact": notification.contact,
            }

            send_push_notification(
                user=user,
                title=f"New Delivery: {notification.source} to {notification.destination}",
                body=notification.message,
                data=notification_data,
                )

            response["status"] = 201
            response["message"] = "Notification created successfully"
            response["notification_id"] = str(notification.id)
            response["vehicle_id"] = str(vehicle_id)

        response["status"] = 400
        response["message"] = "Invalid data"

    def handle_bulk_create(self, request):
        response = {"status": 400}
        try:
            # Transform data if coming in the {0: {...}, 1: {...}} format
            if isinstance(request.data.get('notifications'), dict):
                request.data['notifications'] = list(
                    request.data['notifications'].values())

            bulk_serializer = BulkVehicleNotificationSerializer(
                data=request.data)
            if not bulk_serializer.is_valid():
                response["status"] = 400
                response["message"] = "Invalid data"

            vehicle_ids = bulk_serializer.validated_data['vehicle_ids']
            notifications_data = bulk_serializer.validated_data['notifications']

            created_notifications = []
            errors = []

            for vehicle_id in vehicle_ids:
                vehicle = VehicleInfo.objects.get(id=vehicle_id)
                user = User.objects.filter(number=vehicle.alternate_number).first()
                if user:
                    user = user.id
                else:
                    response["status"] = 400
                    response["message"] = "User not found"

                for notification_data in notifications_data:
                    # Remove vehicle_id from notification data if present
                    notification_data.pop('vehicle_id', None)

                    notification = DriverNotification.objects.create(
                        vehicle=vehicle,
                        created_by=request.user,
                        **notification_data
                    )

                    # Send push notification with all details
                    notification_data = {
                        "notification_id": str(notification.id),
                        "vehicle_id": str(vehicle_id),
                        "source": notification.source,
                        "destination": notification.destination,
                        "rate": str(notification.rate),
                        "weight": str(notification.weight),
                        "date": str(notification.date) if notification.date else None,
                        "message": notification.message,
                        "contact": notification.contact,
                    }

                    send_push_notification(
                        user=user,
                        title=f"New Delivery: {notification.source} to {notification.destination}",
                        body=notification.message,
                        data=notification_data,
                        )
            
                    created_notifications.append({
                        "id": str(notification.id),
                        "vehicle_id": str(vehicle_id)
                    })
                    response_data = {
                        "created_count": len(created_notifications),
                        "created_notifications": created_notifications,
                        "error_count": len(errors),
                        "errors": errors
                    }
                    status_code = 201 if created_notifications else 400
                    response["status"] = status_code
                    response["data"] = response_data

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)


class GetByIdVehicleNotification(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response = {"status": 400}
        try:
            vehicle_id = request.query_params.get('vehicle_id', None)

            vehicle = VehicleInfo.objects.get(id=vehicle_id)
            notifications = DriverNotification.objects.filter(vehicle=vehicle)

            # Apply optional filters
            is_read = request.query_params.get('is_read')
            if is_read in ['true', 'false']:
                notifications = notifications.filter(
                    is_read=is_read.lower() == 'true')

            # Apply sorting
            sort = request.query_params.get('sort', 'desc')
            if sort == 'asc':
                notifications = notifications.order_by('created_at')
            else:
                notifications = notifications.order_by('-created_at')

            # Apply limit
            limit = request.query_params.get('limit')
            if limit and limit.isdigit():
                notifications = notifications[:int(limit)]

            serializer = GetVehicleNotificationByIdSerializer(
                notifications, many=True)

            response["status"] = 200
            response["vehicle_number"] = vehicle.vehicle_number
            response["count"] = notifications.count()
            response["notifications"] = serializer.data

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)


class LocationLockedNotifications(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response = {"status": 400}
        
        try:
            notifications = DriverNotification.objects.filter(
                Q(location_read_lock=False) |
                Q(is_read=True, reserved_by=request.user)
            ).distinct()

            serializer = NotificationDetailSerializer(notifications, many=True)
            response["status"] = 200
            response["data"] = serializer.data

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)


class MarkNotificationRead(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        response = {"status": 400}

        try:
            notification_id = request.query_params.get('notification_id', None)
            notification = DriverNotification.objects.get(id=notification_id)

            serializer = NotificationReadSerializer(
                notification, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                response["status"] = 200
                response["data"] = NotificationDetailSerializer(
                    notification).data
            else:
                error_data = serializer.errors.get("is_read", {})
                response["status"] = 400
                response["vehicle_id"] = str(error_data.get("vehicle_id", ""))
                response["is_accepted"] = str(error_data.get("is_accepted", ""))
                response["msg"] = str(error_data.get("msg", "Validation error."))
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)


class DeleteVehicleById(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        response = {"status": 400}
        try:
            vehicle_id = request.query_params.get('vehicle_id', None)
            if vehicle_id:
                # Delete all notifications related to the vehicle
                DriverNotification.objects.filter(vehicle_id=vehicle_id).delete()
                # Delete all images/documents related to the vehicle
                VehicleImage.objects.filter(vehicle_id=vehicle_id).delete()
                # Delete the vehicle itself
                vehicle = VehicleInfo.objects.get(id=vehicle_id)
                vehicle.delete()
                response["status"] = 200
                response["message"] = "Vehicle and all related data deleted successfully"

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)

        return Response(response)


class GetAllNotifications(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response = {"status": 400}
        try:
            is_read = request.query_params.get("is_read", None)
            is_accepted = request.query_params.get("is_accepted", None)
            creator_name = request.query_params.get("username", None)
            filter_by_date = request.query_params.get("date", None)

            notifications = DriverNotification.objects.select_related('created_by').all()

            # Apply filters
            if is_read is not None and is_accepted is not None:
                is_read_bool = is_read.lower() == 'true'
                is_accepted_bool = is_accepted.lower() == 'true'

                if is_read_bool and is_accepted_bool:
                    # Read notifications
                    notifications = notifications.filter(
                        is_read=True,
                        is_accepted=True,
                    )

                elif is_accepted_bool and not is_read_bool:
                    # Rejected notifications
                    notifications = notifications.filter(
                        is_read=False,
                        is_accepted=True,
                    )

                elif not is_read_bool and not is_accepted_bool:
                    # Unread notifications
                    notifications = notifications.filter(
                        is_read=False,
                        is_accepted=False,
                    )
            
            if creator_name:
                notifications = notifications.filter(
                    created_by__name=creator_name
                )

            if filter_by_date:
                filter_date = datetime.strptime(filter_by_date, "%Y-%m-%d").date()
                notifications = notifications.filter(
                    date=filter_date
                )

            creator_ids = notifications.values_list('created_by', flat=True).distinct()
            creators = User.objects.filter(id__in=creator_ids)

            serializer = NotificationDetailSerializer(notifications, many=True)
            filtered_data = [
                item for item in serializer.data
                if not (item.get("is_read") is False and item.get("is_accepted") is True)
            ]
            creator_serializer = UserBasicSerializer(creators, many=True)
            response["status"] = 200
            response["data"] = filtered_data
            response["creators"] = creator_serializer.data

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)


class GetReadNotifications(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response = {"status": 400}
        try:
            notifications = DriverNotification.objects.filter(is_read=True)
            serializer = ReadNotificationSerializer(notifications, many=True)
            response["status"] = 200
            response["data"] = serializer.data

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)

class UpdateNotificationById(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        response = {"status": 400}

        try:
            notification_id = request.query_params.get('notification_id', None)
            notification = DriverNotification.objects.get(id=notification_id)
            if not (notification.is_read and notification.is_accepted):
                response["status"] = 400
                response["message"] = "notification update only if is_read and is_accepted"

            else:
                serializer = UpdateNotificationByIdSerializer(notification, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    response["status"] = 200
                    response["message"] = UpdateNotificationByIdSerializer(notification).data

        except Exception as e:
                error = f"\nType: {type(e).__name__}"
                error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
                error += f"\nLine: {e.__traceback__.tb_lineno}"
                error += f"\nMessage: {str(e)}"
                logger.error(error)
        return Response(response)

class BulkDeleteNotifications(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        response = {"status": 400}

        try:
            notification_ids = request.query_params.get('notification_ids', [])
            if not notification_ids:
                response["status"] = 400
                response["message"] = "No notification IDs provided"
            
            valid_notifications = []
            invalid_ids = []

            for notification_id in notification_ids.split(","):
                try:
                    notifications = DriverNotification.objects.get(id=notification_id)
                    valid_notifications.append(notifications)
                except (ValueError, DriverNotification.DoesNotExist):
                    invalid_ids.append(notification_id)
            if invalid_ids:
                response["status"] = 400
                response["message"] = "Notification IDs are invalid"

            if valid_notifications:
                for notification in valid_notifications:
                    notification.delete()
                    response["status"] = 200
                    response["message"] = "Notification deleted successfully"

        except Exception as e:
                error = f"\nType: {type(e).__name__}"
                error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
                error += f"\nLine: {e.__traceback__.tb_lineno}"
                error += f"\nMessage: {str(e)}"
                logger.error(error)
        return Response(response)


class GetNotificationByIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response = {"status": 400}

        try:
            notification_id = request.query_params.get('notification_id', None)
            if not notification_id:
                response["status"] = 400
                response["message"] = "No notification ID provided"
            notification = DriverNotification.objects.get(id=notification_id)
            serializer = NotificationDetailSerializer(notification)
            if serializer:
                response["status"] = 200
                response["notification"] = serializer.data

        except Exception as e:
                error = f"\nType: {type(e).__name__}"
                error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
                error += f"\nLine: {e.__traceback__.tb_lineno}"
                error += f"\nMessage: {str(e)}"
                logger.error(error)
        return Response(response)
    

class RegisterFCMDeviceView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self, request, *args, **kwargs):
        response = { "status": 400 }

        try:
            token = request.query_params.get("token", None)
            device_id = request.query_params.get("device_id", None)

            if not token:
                response["status"] = 400
                response["message"] = "Token is required"

            device, created = UserFCMDevice.objects.update_or_create(
                registration_id=token,
                defaults={
                    "user": request.user if request.user.is_authenticated else None,
                    "device_id": device_id,
                    "active": True,
                }
            )

            response["status"] = 200
            response["created"] = created
            response["device_id"] = device.id

        except Exception as e:
                error = f"\nType: {type(e).__name__}"
                error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
                error += f"\nLine: {e.__traceback__.tb_lineno}"
                error += f"\nMessage: {str(e)}"
                logger.error(error)
        return Response(response)

class CreateDisplayPermissionsView(APIView):
    permission_classes=[IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        response = { "status": 400 }

        try:
            role = request.data.get("role", None)
            items = request.data.get("items", [])

            if role not in ['staff', 'admin']:
                response["status"] = 400
                response["message"] = "Role must be either 'staff' or 'admin'"

            if not items:
                response["status"] = 400
                response["message"] = "Items list cannot be empty."

            # Get all users of this role
            users = User.objects.filter(role=role)

            # First remove all existing permissions for this role
            Display.objects.filter(user__role=role).delete()

            for user in users:
                for item in items:
                    Display.objects.get_or_create(user=user, items=item)

            # Also set default permissions for future users
            role_config, created = RolePermissionConfig.objects.get_or_create(
                role=role,
                defaults={'items': items}
            )
            if not created:
                role_config.items = items
                role_config.save()

            response["status"] = 201
            response["message"] = f"Permissions updated for {len(users)} {role} users"

        except Exception as e:
                error = f"\nType: {type(e).__name__}"
                error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
                error += f"\nLine: {e.__traceback__.tb_lineno}"
                error += f"\nMessage: {str(e)}"
                logger.error(error)
        return Response(response)
    
class GetDisplayPermissionsView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response = { "status": 400 }

        try:
            role = request.query_params.get("role", None)

            if role not in ['staff', 'admin']:
                response["status"] = 400
                response["message"] = "Role parameter must be either 'staff' or 'admin'"

            if role == "staff":
                users = User.objects.filter(role="staff")
            else:
                users = User.objects.filter(role="admin")

            roles_and_items = []
            for user in users:
                accessible_items = Display.get_user_items(user)
                roles_and_items.append({
                    "role": user.role,
                    "items": accessible_items
                })

            response["status"] = 200
            response["data"] = roles_and_items

        except Exception as e:
                error = f"\nType: {type(e).__name__}"
                error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
                error += f"\nLine: {e.__traceback__.tb_lineno}"
                error += f"\nMessage: {str(e)}"
                logger.error(error)
        return Response(response)
    
class VerifyDocumentView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self, request, *args, **kwargs):
        response = { "status": 400 }

        try:
            vehicle_id = request.query_params.get("vehicle_id", None)
            image_ids = request.data.get("image_ids", [])

            if not vehicle_id:
                response["status"] = 400
                response["message"] = "User not found"
            
            if not image_ids or not isinstance(image_ids, list):
                response["status"] = 400
                response["message"] = "Image not found"
            
            vehicle_uuid = uuid.UUID(vehicle_id)
            image_uuids = [uuid.UUID(img_id) for img_id in image_ids]

            vehicle = VehicleInfo.objects.get(id=vehicle_uuid)
            vehicle_images = VehicleImage.objects.filter(vehicle=vehicle)
            existing_image_ids = set(vehicle_images.values_list('id', flat=True))
            provided_image_ids = set(image_uuids)

            # Keep only matching image_ids, delete others
            valid_image_ids = existing_image_ids.intersection(provided_image_ids)
            images_to_delete = vehicle_images.exclude(id__in=valid_image_ids)
            deleted_count = images_to_delete.count()
            images_to_delete.delete()

            vehicle.update_status()

            if vehicle.images.count() >= 6:
                vehicle.status = vehicle.StatusChoices.COMPLETED
                vehicle.save(update_fields=["status"])
            elif vehicle.images.count() == 0:
                vehicle.status = vehicle.StatusChoices.IN_COMPLETE
                vehicle.save(update_fields=["status"])
            else:
                vehicle.status = vehicle.StatusChoices.IN_PROGRESS
                vehicle.save(update_fields=["status"])

            response["status"] = 200
            response["message"] = "Verification complete"
            response["kept_image_ids"] = list(valid_image_ids)
            response["deleted_count"] = deleted_count
            response["vehicle_status"] = vehicle.status

        except Exception as e:
                error = f"\nType: {type(e).__name__}"
                error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
                error += f"\nLine: {e.__traceback__.tb_lineno}"
                error += f"\nMessage: {str(e)}"
                logger.error(error)
        return Response(response)