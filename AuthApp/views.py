from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from AuthApp.models import Driver
from AuthApp.utils import send_otp_api, verify_detail, verify_otp, get_location

from AdminApp.models import User
from AdminApp.views import get_tokens_for_user

from MemberApp.models import VehicleInfo
from MemberApp.views import IsAdminUser

from AuthApp.serializers import GetAllDriversInfoSerailizer, UpdateDriverInfoSerializer, DriverDetailSerializer

import logging

logger = logging.getLogger(__name__)


class SignUpAPI(APIView):
    def post(self, request, auth_type, *args, **kwargs):
        data = request.data
        full_name = data.get("full_name")
        email = data.get("email")
        number = data.get("number")

        # Check for missing fields
        missing_fields = []
        if not full_name:
            missing_fields.append("full_name")
        if not email:
            missing_fields.append("email")
        if not number:
            missing_fields.append("number")

        if missing_fields:
            return Response(
                {"status": 400,
                    "msg": f"Missing fields: {', '.join(missing_fields)}"}
            )

        # Check for existing email/phone
        if (
            Driver.objects.filter(
                Q(email__iexact=email.lower()) | Q(number=number)
            ).exists()
            or VehicleInfo.objects.filter(alternate_number=number).exists()
        ):
            return Response(
                {"status": 400, "msg": "Email or phone number already exists."}
            )

        try:
            # Create user and driver
            number = number[-10:]
            if len(number) != 10:
                return Response({"status": 400, "msg": "Invalid phone number format."})
            if not number.isdigit():
                return Response({"status": 400, "msg": "Phone number must be numeric."})

            user = User.objects.create(
                name=full_name, email=email, number=number, is_active=True)
            Driver.objects.get_or_create(
                name=full_name, email=email, number=number)
            token = get_tokens_for_user(user=user)

            return Response(
                {"status": 200, "msg": "Registration successfull", "token": token}
            )

        except Exception as e:
            logger.error("Signup error", exc_info=True)
            return Response({"status": 500, "msg": "An error occurred during signup."})


class SignOutAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        response = {"status": 400}
        try:
            refresh = request.data.get("token")
            if refresh:
                token = RefreshToken(refresh)
                token.blacklist()
                response["status"] = 200
        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)


class SendOtpAPI(APIView):
    def post(self, request):
        response = {"status": 400}
        try:
            phone_number = request.data.get("phone")
            if not phone_number:
                response["msg"] = "Phone number is required."
                return Response(response)

            # Check if the number exists for a driver or a vehicle
            driver_exists, vehicle_exists = verify_detail(phone_number)

            if not driver_exists and not vehicle_exists:
                return Response(
                    {"status": 404, "msg": "This number is not registered."}
                )

            # Send OTP
            otp_response = send_otp_api(phone_number)

            if otp_response.get("type") == "success":
                return Response({"status": 200, "msg": "OTP sent successfully."})
            else:
                return Response(
                    {"status": 500, "msg": "Failed to send OTP. Please try again."}
                )

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)


class VerifyOtpAPI(APIView):
    def post(self, request):
        response = {"status": 400}
        try:
            phone_number = request.data.get("phone")
            otp = request.data.get("otp")

            if not phone_number or not otp:
                return Response(
                    {"status": 400, "msg": "Phone number and OTP are required."}
                )

            # Check if the number exists for a driver or a vehicle
            driver_exists, vehicle_exists = verify_detail(phone_number)

            if not driver_exists and not vehicle_exists:
                return Response(
                    {"status": 400, "msg": "This number is not registered."}
                )

            # Verify OTP
            verify_otp_status = verify_otp(phone_number, otp)

            if verify_otp_status.get("type", None) != "success":
                response["msg"] = "Invalid OTP."
                return Response(response)

            user = None
            response.update({"Vehicle": False, "Document": False})

            if driver_exists:
                user_obj = Driver.objects.get(number=driver_exists)
                user = User.objects.filter(email=user_obj.email).first()

                vehicle = VehicleInfo.objects.filter(
                    alternate_number=user_obj.number
                ).first()
                if vehicle:
                    response.update(
                        {
                            "vehicle_id": vehicle.id,
                            "phone": vehicle.alternate_number,
                            "Vehicle": True,
                            "Document": vehicle.status == "COMPLETED",
                        }
                    )

            elif vehicle_exists:
                # TODO: create email field in vehicle info
                pass

            if user:
                token = get_tokens_for_user(user=user)
                response.update(
                    {"status": 200, "msg": "OTP verified successfully.", "token": token}
                )

        except Exception as e:
            error = (
                f"\nType: {type(e).__name__}"
                f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
                f"\nLine: {e.__traceback__.tb_lineno}"
                f"\nMessage: {str(e)}"
            )
            logger.error(error)

        return Response(response)


class ProfileDocsStatusAPI(APIView):
    def get(self, request):
        response = {"status": 400}

        try:
            phoneNumber = request.query_params.get("phone")
            if not phoneNumber:
                response["status"] = 400
                response["msg"] = "Phone number is required."
                return Response(response)

            user_info = VehicleInfo.objects.filter(
                alternate_number=phoneNumber).first()

            if user_info:
                response["status"] = 200
                response["Document"] = user_info.status
            else:
                response["status"] = 404
                response["msg"] = "Vehicle not found."

        except Exception as e:
            # Catch and log any exceptions
            logger.error(f"Error occurred: {str(e)}", exc_info=True)
            response["status"] = 500
            response["msg"] = "Internal server error."

        return Response(response)


class UpdateLocationAPI(APIView):
    def post(self, request):
        response = {"status": 400}
        try:
            phone_number = request.data.get("phone")
            latitude = request.data.get("latitude")
            longitude = request.data.get("longitude")
            status = request.data.get("location_status")

            if not phone_number or not latitude or not longitude:
                response["msg"] = "Phone number, latitude, and longitude are required."
                return Response(response)

            valid_statuses = {"ON_LOCATION", "OFF_LOCATION", "IN_TRANSIT"}
            if status not in valid_statuses:
                response["msg"] = (
                    f"Invalid location_status. Allowed values: {valid_statuses}"
                )
                return Response(response)

            vehicle_info = VehicleInfo.objects.filter(
                alternate_number=phone_number
            ).first()

            if vehicle_info:
                get_location_response = get_location(latitude, longitude)
                if not get_location_response:
                    return Response({"status": 500, "msg": "Failed to get location."})

                vehicle_info.address = get_location_response
                vehicle_info.location_status = status
                vehicle_info.save()

                response["status"] = 200
                response["msg"] = "Location updated successfully."
            else:
                response["status"] = 404
                response["msg"] = "Vehicle not found."

        except Exception as e:
            logger.error(f"Error occurred: {str(e)}", exc_info=True)
            response["status"] = 500
            response["msg"] = "Internal server error."

        return Response(response)


class UserProfile(APIView):
    def get(self, request):
        response = {"status": 400}
        user_phone = request.query_params.get("phone")

        if not user_phone:
            response["msg"] = "Phone number is required."
            return Response(response)

        try:
            # Get the associated vehicle info
            vehicle_info = VehicleInfo.objects.filter(
                alternate_number=user_phone
            ).first()

            if vehicle_info:
                # Get related capacity and driver info
                capacity = vehicle_info.capacity
                driver_info = Driver.objects.filter(number=user_phone).first()

                if driver_info and capacity:
                    response["status"] = 200
                    response["msg"] = "Driver profile retrieved successfully."
                    response["data"] = {
                        "driver_name": driver_info.name,
                        "driver_email": driver_info.email,
                        "vehicle_capacity": capacity.capacity,
                        "owner_number": vehicle_info.number,
                        "your_number": vehicle_info.alternate_number,
                        "address": vehicle_info.address,
                        "vehicle_number": vehicle_info.vehicle_number,
                        "vehicle_type": vehicle_info.vehicle_type,
                        "owner_name": vehicle_info.name,
                        # Uncomment if needed
                        # "vehicle_image": vehicle_info.image.url if vehicle_info.image else None,
                    }
                else:
                    response["status"] = 400
                    response["msg"] = "Driver not found."
            else:
                response["status"] = 400
                response["msg"] = "Vehicle not found."

        except Exception as e:
            logger.error(f"Error occurred: {str(e)}", exc_info=True)
            response["status"] = 500
            response["msg"] = "Internal server error."

        return Response(response)


class DeleteDriverAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        response = {"status": 400}
        try:
            driver_id = request.query_params.get('driver_id', None)
            user = User.objects.filter(id=driver_id).first()
            if user:
                user.delete()

            driver = Driver.objects.filter(number=user.number).first()
            if driver:
                # Check if the driver is associated with any vehicle
                vehicle_info = VehicleInfo.objects.filter(
                    alternate_number=driver.number
                ).first()

                if vehicle_info:
                    response["status"] = 400
                    response["msg"] = "Driver cannot be deleted as they are associated with a vehicle."
                    return Response(response)

            if driver:
                driver.delete()
                response["status"] = 200
                response["msg"] = "Driver deleted successfully."

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)

        return Response(response)


class GetAllDriverInfo(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        response = {"status": 400}
        try:
            driver_info = Driver.objects.all()
            if not driver_info:
                response["status"] = 400
                response["message"] = "Driver not found"
            else:
                serializer = GetAllDriversInfoSerailizer(driver_info, many=True)
                data = serializer.data
                response["status"] = 200
                response["drivers"] = data

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)
    
class UpdateDriverById(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        response = {"status": 400}
        try:
            driver_id = request.query_params.get('driver_id', None)
            driver = Driver.objects.filter(id=driver_id).first()
            if not driver_id:
                response["status"] = 400
                response["message"] = "Driver not found"
            else:
                serializer = UpdateDriverInfoSerializer(driver, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    response["status"] = 200
                    response["driver"] = serializer.data
            
        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)
    
class GetDriverByIdView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        response = {"status": 400}
        try:
            driver_id = request.query_params.get('driver_id', None)
            driver = Driver.objects.get(id=driver_id)
            if not driver:
                response["status"] = 400
                response["message"] = "Driver not found"
            else:
                serializer = DriverDetailSerializer(driver)
                data = serializer.data
                response["status"] = 200
                response["drivers"] = data

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)

class DeleteDriverByIdAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        response = {"status": 400}
        try:
            driver_id = request.query_params.get('driver_id', None)
            driver = Driver.objects.get(id=driver_id)
            if not driver:
                response["status"] = 400
                response["message"] = "Driver not found"
            user = User.objects.filter(number=driver.number).first()
            if user:
                user.delete()
            else:
                response["status"] = 400
                response["message"] = "User not found"

            driver = Driver.objects.filter(number=user.number).first()
            if driver:
                # Check if the driver is associated with any vehicle
                vehicle_info = VehicleInfo.objects.filter(
                    alternate_number=driver.number
                ).first()

                if vehicle_info:
                    response["status"] = 400
                    response["message"] = "Driver cannot be deleted as they are associated with a vehicle."

            if driver:
                driver.delete()
                response["status"] = 200
                response["message"] = "Driver deleted successfully."

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)