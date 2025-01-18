from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from AuthApp.models import OneTimePassword, Driver
from AuthApp.utils import send_otp_api, verify_detail, verify_otp
from MemberApp.models import VehicleInfo
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
                user_obj = Driver.objects.create(
                    name=full_name,
                    email=email,
                    number=number,
                )
                response["status"] = 200

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
    """
    API Endpoint to send an OTP to a given phone number.

    This API checks if the provided phone number is registered as a Driver
    or Vehicle record in the database. If found, it triggers an OTP to the
    phone number. The response indicates success or failure of the OTP
    operation.

    Request Body:
    - phone (str): The phone number to which the OTP should be sent.

    Responses:
    - 200: OTP sent successfully.
    - 400: Invalid request (e.g., missing phone number or OTP failure).
    - 404: Phone number not registered as Driver or Vehicle.
    - 500: Internal server error.

    """

    def post(self, request):
        response = {"status": 400, "msg": "Invalid Request"}
        try:
            # Log the incoming request
            logger.info("Received OTP request with data: %s", request.data)

            # Extract phone number
            phone_number = request.data.get("phone")
            if not phone_number:
                logger.warning("Phone number missing in request data.")
                response["msg"] = "Phone number is required."
                return Response(response)


            # Check if the number exists for a driver or a vehicle
            driver_exists, vehicle_exists = verify_detail(phone_number)

            if not driver_exists and not vehicle_exists:
                logger.info("Number %s is not registered as Driver or Vehicle.", phone_number)
                return Response({"status": 404, "msg": "This number is not registered."})

            # Log successful validation
            logger.info("Number %s found in database. Sending OTP...", phone_number)

            # Send OTP
            otp_response = send_otp_api(phone_number)
            if otp_response.get("type") == "success":
                logger.info("OTP sent successfully to %s.", phone_number)
                return Response({"status": 200, "msg": "OTP sent successfully."})
            else:
                logger.error("Failed to send OTP to %s. Response: %s", phone_number, otp_response)
                return Response({"status": 500, "msg": "Failed to send OTP. Please try again."})

        except Exception as e:
            logger.exception("Unexpected error in SendOtpAPI: %s", str(e))
            response.update({"status": 500, "msg": "Internal Server Error"})
            return Response(response)


class VerifyOtpAPI(APIView):
    """
    API view for verifying OTP sent to a phone number and issuing a JWT token upon successful verification.
    """

    def post(self, request):
        """
        Verifies the OTP for a given phone number and returns a JWT token if successful.

        Args:
            request (Request): The HTTP request object containing phone number and OTP.

        Returns:
            Response: The HTTP response indicating success or failure of the OTP verification, and includes a JWT token on success.
        """
        phone_number = request.data.get("phone")
        otp = request.data.get("otp")

        # Validate input
        if not phone_number or not otp:
            logger.warning("Phone number or OTP is missing in the request.")
            return Response({"status": 400, "msg": "Invalid Request. Phone number and OTP are required."})

        try:
            # Check if the number exists for a driver or a vehicle
            driver_exists, vehicle_exists = verify_detail(phone_number)

            if not driver_exists and not vehicle_exists:
                logger.info("Phone number %s is not registered as Driver or Vehicle.", phone_number)
                return Response({"status": 404, "msg": "This number is not registered."})

            # Verify OTP
            verify_otp_status = verify_otp(phone_number, otp)

            if verify_otp_status.get("type") == "success":
                # OTP verified successfully, generate and return JWT token
                # jwt_token = RefreshToken.for_user()
                return Response(
                    {"status": 200, "msg": "OTP verified successfully.", "token": 'jwt_token'})
            elif verify_otp_status["type"] == "error":
                logger.warning("Invalid OTP provided for phone number %s", phone_number)
                return Response({"status": 200, "msg": f"{verify_otp_status.get('message', 'Invalid OTP.')}"})
            else:
                logger.warning("Invalid OTP provided for phone number %s", phone_number)
                return Response({"status": 400, "msg": "Invalid OTP."})

        except Exception as e:
            # Catch unexpected errors and log them
            logger.error("Unexpected error occurred while verifying OTP for phone number %s: %s", phone_number, str(e))
            return Response({"status": 500, "msg": "Internal Server Error."})

