from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from AuthApp.models import Driver
from AuthApp.utils import send_otp_api, verify_detail, verify_otp

from AdminApp.models import User
from AdminApp.views import get_tokens_for_user

from MemberApp.models import VehicleInfo, VehicleImage

import logging

logger = logging.getLogger(__name__)

class SignUpAPI(APIView):
    def post(self, request, auth_type, *args, **kwargs):
        response = {"status": 400}
        try:
            full_name = request.data.get("full_name")
            email = request.data.get("email")
            number = request.data.get("number")

            # validate required fields
            if not full_name or not email or not number:
                response["status"] = 400

            if Driver.objects.filter(Q(email=email) | Q(number=number)).exists():
                response["status"] = 400

            if VehicleInfo.objects.filter(number=number).exists():
                response["status"] = 400
            else:
                user_obj = User.objects.create(
                    name=full_name, email=email, is_active=True)
                Driver.objects.get_or_create(
                    name=full_name,
                    email=email,
                    number=number,
                )
                response["status"] = 200
                token = get_tokens_for_user(user=user_obj)
                response["token"] = token

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
            logger.error(error)
        return Response(response)

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
                return Response({"status": 404, "msg": "This number is not registered."})

            # Send OTP
            otp_response = send_otp_api(phone_number)

            if otp_response.get("type") == "success":
                return Response({"status": 200, "msg": "OTP sent successfully."})
            else:
                return Response({"status": 500, "msg": "Failed to send OTP. Please try again."})

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
                return Response({"status": 400, "msg": "Phone number and OTP are required."})

            # Check if the number exists for a driver or a vehicle
            driver_exists, vehicle_exists = verify_detail(phone_number)

            if not driver_exists and not vehicle_exists:
                return Response({"status": 404, "msg": "This number is not registered."})

            # Verify OTP
            verify_otp_status = verify_otp(phone_number, otp)

            if verify_otp_status.get("type") == "success":
                if driver_exists:
                    user_obj = Driver.objects.get(number=driver_exists)
                    if user_obj:
                        user = User.objects.filter(
                            email=user_obj.email).first()
                        vehicle_exist = VehicleInfo.objects.filter(
                            number=user_obj.number).first()
                        if vehicle_exist:
                            document_exist = vehicle_exist.status

                        if vehicle_exist:
                            response["vehicle_id"] = vehicle_exist.id
                            response["phone"] = vehicle_exist.number
                            response["Vehicle"] = True
                            if document_exist == "COMPLETED":
                                response["Document"] = True
                            else:
                                response["Document"] = False
                        else:
                            response["Vehicle"] = False
                            response["Document"] = False

                elif vehicle_exists:
                    # TODO: create email field in vehicle info
                    pass

                token = get_tokens_for_user(user=user)
                response["status"] = 200
                response["msg"] = "OTP verified successfully."
                response["token"] = token

        except Exception as e:
            error = f"\nType: {type(e).__name__}"
            error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
            error += f"\nLine: {e.__traceback__.tb_lineno}"
            error += f"\nMessage: {str(e)}"
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

            user_info = VehicleInfo.objects.filter(number=phoneNumber).first()

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
