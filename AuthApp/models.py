from django.db import models
from django.utils import timezone
import uuid

import logging

# Create your models here.

logger = logging.getLogger(__name__)


class OneTimePassword(models.Model):
    reference_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)

    mobile_number = models.CharField(max_length=100, blank=True, null=True)

    created = models.DateTimeField(default=timezone.now)

    otp = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"

    def __str__(self):
        return f"{self.reference_id} - {self.mobile_number} - {self.otp}"

    def is_expired(self):
        if (timezone.now() - self.created).seconds > 300:
            return True
        return False

    def save(self, *args, **kwargs):
        self.created = timezone.now()
        return super(OneTimePassword, self).save(*args, **kwargs)


class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    number = models.CharField(max_length=15, unique=True)

    vehicle_info = models.CharField(max_length=100, blank=True, null=True)

    is_deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Driver"
        verbose_name_plural = "Drivers"

    def user_id(self):
        return str(self.id)[:8]

    def vehicle_number(self):
        return str(self.vehicle_info)

    def __str__(self):
        return f"{self.email} {self.vehicle_info}"

    def save(self, *args, **kwargs):
        return super(Driver, self).save(*args, **kwargs)
