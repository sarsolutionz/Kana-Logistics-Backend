from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveAPIView
from rest_framework.parsers import MultiPartParser, JSONParser

from AdminApp.renderers import UserRenderer

from django.db import IntegrityError

from MemberApp.models import VehicleInfo, VehicleCapacity, VehicleImage

from MemberApp.serializers import CreateVehicleInfoSerializer, GetAllVehicleInfoSerializer, \
    GetByIdVehicleInfoSerializer, UpdateVehicleInfoByIDSerializer, VehicleCapacitySerializer, \
    CreateVehicleCapacitySerializer, CreateDocumentSerializer, DeleteDocumentSerializer, \
    VehicleImageSerializer

import logging

logger = logging.getLogger(__name__)


# Create your views here.


class CreateVehicleAPI(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CreateVehicleInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle_info = serializer.save()
        vehicle_id = vehicle_info.id
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
    permission_classes = [IsAuthenticated]

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
    parser_classes = [JSONParser, MultiPartParser]  # Ensure multipart parser is used

    def post(self, request, *args, **kwargs):
        serializer = CreateDocumentSerializer(data=request.data, context={'request': request})
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
    permission_classes = [IsAuthenticated]

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
