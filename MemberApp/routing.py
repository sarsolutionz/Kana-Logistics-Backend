from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/vehicleinfo/$", consumers.VehicleInfoConsumer.as_asgi()),
]
