from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveAPIView

from AdminApp.renderers import UserRenderer

from django.db import IntegrityError

from MemberApp.models import VehicleInfo, VehicleCapacity

from MemberApp.serializers import CreateVehicleInfoSerializer, GetAllVehicleInfoSerializer, GetByIdVehicleInfoSerializer, UpdateVehicleInfoByIDSerializer, VehicleCapacitySerializer, CreateVehicleCapacitySerializer

import logging

logger = logging.getLogger(__name__)

# Create your views here.


class CreateVehicleAPI(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CreateVehicleInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Vehicle information created successfully"}, status=status.HTTP_201_CREATED)


class GetAllVehicleInfoAPI(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            vehicles = VehicleInfo.objects.all()
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
