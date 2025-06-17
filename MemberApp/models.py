from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.conf import settings
from datetime import timedelta, timezone
import uuid

# Create your models here.


class VehicleCapacity(models.Model):
    capacity = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        validators=[MinValueValidator(0.1)],    # Ensure capacity is positive
        unique=True,
    )

    @property
    def description(self):
        return f"{self.capacity} T.N"

    def __str__(self):
        return self.description


class VehicleInfo(models.Model):
    # UUID as primary key for the image
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    VEHICLE_TYPE_CHOICES = [
        ('', 'Select an option'),  # Placeholder option
        ('open', 'Open'),
        ('close', 'Close'),
        ('container', 'Container'),
    ]

    class StatusChoices(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        IN_COMPLETE = "IN_COMPLETE", "Incomplete"
        COMPLETED = "COMPLETED", "Completed"

    class LocationStatusChoices(models.TextChoices):
        ON_LOCATION = "ON_LOCATION", "On Location"
        OFF_LOCATION = "OFF_LOCATION", "Off Location"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"

    model = models.CharField(max_length=200, blank=True)

    capacity = models.ForeignKey(
        VehicleCapacity, on_delete=models.SET_NULL, null=True)

    name = models.CharField(max_length=200, blank=True)

    number = models.CharField(max_length=15, blank=True)

    alternate_number = models.CharField(max_length=15, unique=True, blank=True)

    address = models.CharField(max_length=1000, blank=True)

    vehicle_type = models.CharField(
        max_length=10,
        choices=VEHICLE_TYPE_CHOICES,
        default='IN_COMPLETE',
    )

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.IN_COMPLETE
    )

    location_status = models.CharField(
        max_length=20,
        choices=LocationStatusChoices.choices,
        default=LocationStatusChoices.OFF_LOCATION,
    )

    vehicle_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,  # Temporary: allow nulls to update existing rows
        validators=[RegexValidator(
            r'^[A-Z]{2}-\d{2}-[A-Z]{2}-\d{4}$',
            'Enter a valid vehicle number (e.g., GJ-05-ES-9658)'
        )],
    )

    def update_status(self, save_instance=True):
        self.refresh_from_db()
        image_count = self.images.count()

        if image_count == 0:
            self.status = self.StatusChoices.IN_COMPLETE

        if self.status != self.StatusChoices.COMPLETED:
            if image_count >= 1:
                self.status = self.StatusChoices.IN_PROGRESS

        if save_instance:
            self.save(update_fields=["status"])

    class Meta:
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles Info"

    def __str__(self):
        return f"{self.model} {self.name} {self.capacity} ({self.vehicle_type} - {self.vehicle_number} - {self.location_status})"

    def save(self, *args, **kwargs):
        # Check if the specified capacity exists, or create a new one
        if not self.capacity_id:
            # Replace `desired_capacity_value` with the actual desired capacity
            capacity_value = self.capacity.capacity
            capacity_obj, created = VehicleCapacity.objects.get_or_create(
                capacity=capacity_value
            )
            self.capacity = capacity_obj
        super(VehicleInfo, self).save(*args, **kwargs)


# New Image Model for Docs images
def get_image_upload_path(instance, filename):
    """Generate dynamic upload path for vehicle images."""
    return f"docs/{instance.vehicle.id}/{filename}"


class VehicleImage(models.Model):
    """Model to store images for vehicles."""

    # UUID as primary key for the image
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    vehicle = models.ForeignKey(
        'VehicleInfo',
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=get_image_upload_path, blank=False)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Vehicle Image'
        verbose_name_plural = 'Vehicle Images'
        ordering = ['vehicle']

    def __str__(self):
        """Return a string representation of the image."""
        return f"Image ({self.id})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.vehicle.update_status()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.vehicle.update_status()

    def clean(self):
        """Override the clean method to add custom validation if needed."""
        # Add any custom validation for the description or image size if required
        pass


class DriverNotification(models.Model):
    """Model to store driver notifications."""

    # UUID as primary key for the notification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    vehicle = models.ForeignKey(
        'VehicleInfo',
        related_name='notifications',
        on_delete=models.CASCADE
    )
    source = models.CharField(max_length=255, blank=True)
    destination = models.CharField(max_length=255, blank=True)
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        validators=[MinValueValidator(0.01)],  # Ensure rate is positive
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        validators=[MinValueValidator(0.01)],  # Ensure weight is positive
    )
    date = models.DateField(blank=True, null=True)
    message = models.TextField(blank=False)
    contact = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(
            r'^\+?1?\d{9,15}$',
            'Enter a valid phone number (e.g., +919876543210)'
        )],
    )
    is_read = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    location_read_lock = models.BooleanField(default=False)

    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='driver_notifications',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    reservation_time = models.DateTimeField(null=True, blank=True)
    # 15 minutes reservation timeout
    RESERVATION_TIMEOUT = timedelta(minutes=15)

    @property
    def is_reserved(self):
        """Check if the notification is reserved."""
        return self.reserved_by is not None and (
            self.reservation_time + self.RESERVATION_TIMEOUT > timezone.now()
        )

    def reserve(self, user):
        """Reserve the notification for a user."""
        if not self.is_reserved or self.reserved_by == user:
            self.is_read = True
            self.reserved_by = user
            self.reservation_time = timezone.now()
            self.save()
            return True
        return False

    def unreserve(self):
        """Unreserve the notification."""
        if self.is_reserved:
            self.reserved_by = None
            self.reservation_time = None
            self.save()
            return True
        return False

    class Meta:
        verbose_name = 'Driver Notification'
        verbose_name_plural = 'Driver Notifications'
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'destination', 'location_read_lock'],
                name='unique_read_per_location',
                condition=models.Q(location_read_lock=True)
            )
        ]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vehicle', 'is_read']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        """Return a string representation of the notification."""
        return f"Notification ({self.id}) for {self.vehicle}"

    def clean(self):
        if self.is_read and not self.pk:  # New instance being marked read
            if DriverNotification.objects.filter(
                source=self.source,
                destination=self.destination,
                location_read_lock=True
            ).exists():
                raise ValueError(
                    "Another notification for this location is already read")

    def save(self, *args, **kwargs):
        if self.is_read and not self.location_read_lock:
            self.location_read_lock = True
            self.is_accepted = True
        super().save(*args, **kwargs)
