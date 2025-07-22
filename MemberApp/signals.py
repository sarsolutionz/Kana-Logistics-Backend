from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import VehicleInfo, RolePermissionConfig, Display, User
from .serializers import GetAllVehicleInfoSerializer  # or use a manual dict


@receiver(post_save, sender=VehicleInfo)
def vehicleinfo_updated(sender, instance, **kwargs):
    # Serialize the instance
    data = GetAllVehicleInfoSerializer(instance).data

    # Send to WebSocket group
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "vehicleinfo_updates", {"type": "send_vehicleinfo", "data": data}
    )


@receiver(post_save, sender=User)
def apply_default_permissions(sender, instance, created, **kwargs):
    if created:
        try:
            config = RolePermissionConfig.objects.get(role=instance.role)
            for item in config.items:
                Display.objects.get_or_create(user=instance, items=item)
        except RolePermissionConfig.DoesNotExist:
            pass
