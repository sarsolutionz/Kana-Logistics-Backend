from django.db import models
from AdminApp.models import User

import logging
import uuid

# Create your models here.

logger = logging.getLogger(__name__)

class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(User, null=True, blank=True,
                             on_delete=models.SET_NULL)

    name = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    number = models.CharField(max_length=15, unique=True)

    is_deleted = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Driver"
        verbose_name_plural = "Drivers"

    def short_id(self):
        return str(self.id)[:8]

    def __str__(self):
        return f"{self.email} {self.name}"

    def save(self, *args, **kwargs):
        return super(Driver, self).save(*args, **kwargs)