from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
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
    VEHICLE_TYPE_CHOICES = [
        ('', 'Select an option'),  # Placeholder option
        ('open', 'Open'),
        ('close', 'Close')
    ]

    class StatusChoices(models.TextChoices):
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        IN_COMPLETE = "IN_COMPLETE", "Incomplete"
        COMPLETED = "COMPLETED", "Completed"

    model = models.CharField(max_length=200, blank=True)

    capacity = models.ForeignKey(
        VehicleCapacity, on_delete=models.SET_NULL, null=True)

    name = models.CharField(max_length=200, blank=True)

    number = models.CharField(max_length=15, blank=True)

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
        return f"{self.model} {self.name} {self.capacity} ({self.vehicle_type} - {self.vehicle_number})"

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
