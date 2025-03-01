import json
import http.client
from decouple import config

from MemberApp.models import VehicleInfo
from AuthApp.models import Driver
from django.db.models import Q

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

import logging

logger = logging.getLogger(__name__)

# verify from db and validate phone number


def verify_detail(number: str):
    try:
        # Ensure number is valid (non-empty and a valid phone number format)
        if not number or (10 > len(number) > 13):
            raise ValueError("Phone number is invalid or too short.")

        # Trim the number to the last 10 digits
        trimmed_number = number[-10:]
        logger.info("Processing OTP for trimmed number: %s", trimmed_number)

        # Check if the phone number exists in Driver and VehicleInfo models
        driver_exists = Driver.objects.filter(Q(number=trimmed_number)).first()
        vehicle_exists = VehicleInfo.objects.filter(
            Q(number=trimmed_number)).first()

        # Log successful verification
        logger.info("Driver exists: %s, Vehicle exists: %s",
                    driver_exists, vehicle_exists)

        return driver_exists.number if driver_exists else False, vehicle_exists.number if vehicle_exists else False

    except ValueError as ve:
        # Handle invalid phone number format error
        logger.error("Error in verify_detail: %s", str(ve))
        return False or False


# Helper function to send otp
def send_otp_api(number: str):
    template_id = config("TEMP_ID")
    authkey = config("AUTH_KEY")

    # Validate required environment variables
    if not template_id or not authkey:
        error_msg = "TEMP_ID or AUTH_KEY is not set in environment variables."
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    try:
        # Establish HTTPS connection
        conn = http.client.HTTPSConnection("control.msg91.com")

        # Prepare request payload and headers
        payload = json.dumps({
            "Param1": "value1",
            "Param2": "value2",
            "Param3": "value3"
        })
        headers = {'Content-Type': "application/JSON"}

        # Send POST request
        conn.request(
            "POST",
            f"/api/v5/otp?otp_length=6&otp_expiry=5&template_id={template_id}&mobile={
                number.strip()}&authkey={authkey}&realTimeResponse=1",
            payload,
            headers
        )

        # Read and parse response
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        response_data = json.loads(data)

        logger.info(f"OTP API Response: {response_data}")
        return response_data

    except Exception as e:
        # Log detailed error information
        error_msg = (
            f"Error sending OTP: {str(e)}\n"
            f"Type: {type(e).__name__}\n"
            f"File: {e.__traceback__.tb_frame.f_code.co_filename}\n"
            f"Line: {e.__traceback__.tb_lineno}"
        )
        logger.error(error_msg)
        return {"status": "error", "message": "Failed to send OTP due to an internal error."}

    finally:
        # Ensure the connection is closed
        try:
            conn.close()
        except Exception as e:
            logger.warning(f"Error while closing connection: {str(e)}")


# Verify otp from url
def verify_otp(number: str, otp: str):
    try:
        authkey = config("AUTH_KEY")

        conn = http.client.HTTPSConnection("control.msg91.com")

        headers = {'authkey': authkey}

        conn.request(
            "GET", f"/api/v5/otp/verify?otp={otp}&mobile={number}", headers=headers)

        res = conn.getresponse()
        data = res.read().decode("utf-8")
        response_data = json.loads(data)

        logger.info(f"verify API Response: {response_data}")
        return response_data

    except Exception as e:
        # Log detailed error information
        error_msg = (
            f"Error sending OTP: {str(e)}\n"
            f"Type: {type(e).__name__}\n"
            f"File: {e.__traceback__.tb_frame.f_code.co_filename}\n"
            f"Line: {e.__traceback__.tb_lineno}"
        )
        logger.error(error_msg)
        return {"status": "error", "message": "Failed to verify OTP"}
    finally:
        # Ensure the connection is closed
        try:
            conn.close()
        except Exception as e:
            logger.warning(f"Error while closing connection: {str(e)}")
