from django.conf import settings
from rest_framework.response import Response
from MemberApp.models import UserFCMDevice
from firebase_admin import messaging, credentials, initialize_app

import logging

logger = logging.getLogger(__name__)

# Initialize Firebase (one-time)
try:
    cred = credentials.Certificate(settings.FCM_CREDENTIALS)
    initialize_app(cred)

except Exception as e:
        error = f"\nType: {type(e).__name__}"
        error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
        error += f"\nLine: {e.__traceback__.tb_lineno}"
        error += f"\nMessage: {str(e)}"
        logger.error(error)

def send_push_notification(user, title, body, data=None):
    response = { "status": 400 }

    try:
        devices = UserFCMDevice.objects.filter(user=user)
        if not devices.exists():
            response["status"] = 400
            response["message"] = "No active devices found"         

        fcm_tokens = [device.registration_id for device in devices]

        # create a message
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=fcm_tokens,
        )

        # Send message
        res = messaging.send_each_for_multicast(message)

        response["status"] = 200
        response["success_count"] = res.success_count
        response["failure_count"] = res.failure_count
    
    except Exception as e:
        error = f"\nType: {type(e).__name__}"
        error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
        error += f"\nLine: {e.__traceback__.tb_lineno}"
        error += f"\nMessage: {str(e)}"
        logger.error(error)
    return Response(response)
