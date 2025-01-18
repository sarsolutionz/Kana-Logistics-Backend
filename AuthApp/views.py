from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q

from AuthApp.models import OneTimePassword, Driver
from AuthApp.utils import send_otp_api

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

            vehicle_info = VehicleInfo.objects.filter(number=number).first()
            if vehicle_info:
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
