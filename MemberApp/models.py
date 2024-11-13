from django.db import models
from django.core.validators import MinValueValidator, RegexValidator

# Create your models here.


class VehicleCapacity(models.Model):
    capacity = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        validators=[MinValueValidator(0.1)],    # Ensure capacity is positive
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

    model = models.CharField(max_length=200, blank=True)

    capacity = models.ForeignKey(
        VehicleCapacity, on_delete=models.SET_NULL, null=True)

    name = models.CharField(max_length=200, blank=True)

    number = models.CharField(max_length=15, blank=True)

    address = models.CharField(max_length=1000, blank=True)

    vehicle_type = models.CharField(
        max_length=10,
        choices=VEHICLE_TYPE_CHOICES,
        default='',
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
