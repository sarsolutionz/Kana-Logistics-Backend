import json
from channels.generic.websocket import AsyncWebsocketConsumer

class VehicleInfoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("vehicleinfo_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("vehicleinfo_updates", self.channel_name)

    async def send_vehicleinfo(self, event):
        await self.send(text_data=json.dumps(event["data"]))
