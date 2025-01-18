import logging

logger = logging.getLogger(__name__)


def send_otp_api(name, number, otp):
    try:
        pass
    except Exception as e:
        error = f"\nType: {type(e).__name__}"
        error += f"\nFile: {e.__traceback__.tb_frame.f_code.co_filename}"
        error += f"\nLine: {e.__traceback__.tb_lineno}"
        error += f"\nMessage: {str(e)}"
        logger.error(error)
