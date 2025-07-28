import re
import logging
from rest_framework import serializers
from .models import VehicleInfo, VehicleCapacity, VehicleImage, DriverNotification
from AdminApp.models import User

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
import os
from uuid import UUID
from django.conf import settings
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

# Logger setup
logger = logging.getLogger(__name__)


class CreateVehicleInfoSerializer(serializers.ModelSerializer):
    # Adding RegexValidator directly to the vehicle_number field
    vehicle_number = serializers.CharField(
        max_length=255,
        validators=[RegexValidator(
            r'^[A-Z]{2}-\d{2}-[A-Z]{2}-\d{4}$',
            'Enter a valid vehicle number (e.g., GJ-05-ES-9658)'
        )]
    )
    model = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)
    number = serializers.CharField(max_length=255)
    alternate_number = serializers.CharField(max_length=255)
    location_status = serializers.ChoiceField(
        choices=VehicleInfo.LocationStatusChoices.choices,
        default=VehicleInfo.LocationStatusChoices.OFF_LOCATION,
        required=False
    )
    address = serializers.CharField(max_length=255)
    vehicle_type = serializers.ChoiceField(
        choices=[('open', 'Open'), ('close', 'Close'), ('container', 'Container')])
    capacity = serializers.DecimalField(max_digits=4, decimal_places=1)

    class Meta:
        model = VehicleInfo
        fields = ['model', 'name', 'number', 'alternate_number', 'location_status', 'address',
                  'vehicle_type', 'vehicle_number', 'capacity']

    def validate(self, attrs):
        try:
            # Validate required fields
            required_fields = ['model', 'capacity', 'name',
                               'number', 'alternate_number', 'location_status', 'vehicle_number', 'vehicle_type']

            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError(
                        {field: "This field is required."})

            # Validate vehicle_number format
            vehicle_number = attrs.get('vehicle_number')
            if not vehicle_number:
                raise serializers.ValidationError(
                    {'vehicle_number': 'Vehicle number is required.'})
            if not self._validate_vehicle_number(vehicle_number):
                raise serializers.ValidationError(
                    {'vehicle_number': 'Enter a valid vehicle number (e.g., GJ-05-ES-9658)'})

            # Validate and associate capacity
            capacity_value = attrs.get('capacity')
            if capacity_value:
                capacity_obj, created = VehicleCapacity.objects.get_or_create(
                    capacity=capacity_value)
                attrs['capacity'] = capacity_obj
            else:
                raise serializers.ValidationError(
                    {'capacity': 'Capacity is required'})

            location_status = attrs.get('location_status')
            if location_status and location_status not in VehicleInfo.LocationStatusChoices.values:
                raise serializers.ValidationError({
                    'location_status': f'Invalid status. Valid choices are: {dict(VehicleInfo.LocationStatusChoices.choices)}'
                })

            return attrs
        except Exception as e:
            # Log the error
            logger.error(f"Error in validation: {e}")
            raise serializers.ValidationError({'error': str(e)})

    def _validate_vehicle_number(self, vehicle_number):
        """
        Custom method to check vehicle number against the required regex.
        """
        regex = r'^[A-Z]{2}-\d{2}-[A-Z]{2}-\d{4}$'
        if re.match(regex, vehicle_number):
            return True
        return False

    def create(self, validated_data):
        if 'location_status' not in validated_data:
            validated_data['location_status'] = VehicleInfo.LocationStatusChoices.OFF_LOCATION
        try:
            # Create the new VehicleInfo instance if validation is successful
            vehicle_info = VehicleInfo.objects.create(**validated_data)
            return vehicle_info
        except Exception as e:
            logger.error(f"Error in creating vehicle: {e}")
            raise serializers.ValidationError({'error': str(e)})

    def update(self, instance, validated_data):
        try:
            # Update existing vehicle information if validation is successful
            if 'location_status' in validated_data:
                instance.location_status = validated_data['location_status']
            instance.model = validated_data.get('model', instance.model)
            instance.name = validated_data.get('name', instance.name)
            instance.number = validated_data.get('number', instance.number)
            instance.alternate_number = validated_data.get(
                'alternate_number', instance.number)
            instance.vehicle_number = validated_data.get(
                'vehicle_number', instance.vehicle_number)
            instance.vehicle_type = validated_data.get(
                'vehicle_type', instance.vehicle_type)
            instance.capacity = validated_data.get(
                'capacity', instance.capacity)
            instance.save()
            return instance
        except Exception as e:
            logger.error(f"Error in updating vehicle: {e}")
            raise serializers.ValidationError({'error': str(e)})


class GetAllVehicleInfoSerializer(serializers.ModelSerializer):
    # Use SerializerMethodField to return the actual capacity value
    capacity = serializers.SerializerMethodField()

    class Meta:
        model = VehicleInfo
        fields = "__all__"

    def validate_capacity(self, value):
        if not VehicleCapacity.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Selected capacity is invalid.")
        return value

    def get_capacity(self, obj):
        # Assuming 'capacity' is a related field with decimal values like 1.5, 2.5, etc.
        if obj.capacity:
            # Add 'T.N' to the capacity value
            return f"{float(obj.capacity.capacity)} T.N"
        return None


class GetByIdVehicleInfoSerializer(serializers.ModelSerializer):
    # Directly return the capacity as a decimal value
    capacity = serializers.SerializerMethodField()

    class Meta:
        model = VehicleInfo
        fields = "__all__"

    def get_capacity(self, obj):
        # Access the related capacity value and append ' T.N'
        # Assuming capacity is a related model
        return float(obj.capacity.capacity)


class UpdateVehicleInfoByIDSerializer(serializers.ModelSerializer):
    capacity = serializers.DecimalField(
        source='capacity.capacity', max_digits=4, decimal_places=1)
    location_status = serializers.ChoiceField(
        choices=VehicleInfo.LocationStatusChoices.choices,
        required=False
    )

    class Meta:
        model = VehicleInfo
        fields = ['id', 'model', 'name', 'number', 'alternate_number', 'address',
                  'vehicle_type', 'status', 'vehicle_number', 'capacity', 'location_status']

    def validate_vehicle_number(self, value):
        """
        Validate that the vehicle_number is unique, unless the record is being updated and the vehicle_number is not changing.
        """
        vehicle_id = self.instance.id if self.instance else None

        try:
            # If vehicle_number is being updated, check if it's already taken by another vehicle
            if vehicle_id:
                current_vehicle_number = self.instance.vehicle_number
                if current_vehicle_number != value and VehicleInfo.objects.filter(vehicle_number=value).exists():
                    raise serializers.ValidationError(
                        "Vehicle with this vehicle number already exists.")
            else:
                # For new records, just check if vehicle_number is unique
                if VehicleInfo.objects.filter(vehicle_number=value).exists():
                    raise serializers.ValidationError(
                        "Vehicle with this vehicle number already exists.")

            return value
        except Exception as e:
            logger.error(f"Error in updating vehicle: {e}")

    def validate(self, attrs):
        # Validate location_status if provided
        if 'location_status' in attrs:
            if attrs['location_status'] not in VehicleInfo.LocationStatusChoices.values:
                raise serializers.ValidationError({
                    'location_status': f"Invalid status. Choices are: {dict(VehicleInfo.LocationStatusChoices.choices)}"
                })
        return attrs

    def update(self, instance, validated_data):
        capacity_data = validated_data.pop('capacity', None)

        # Handle the capacity update if it exists
        if capacity_data:
            capacity_value = capacity_data['capacity']
            capacity_obj, created = VehicleCapacity.objects.get_or_create(
                capacity=capacity_value)
            instance.capacity = capacity_obj

        if 'status' in validated_data:
            if validated_data['status'] == instance.StatusChoices.COMPLETED:
                instance.status = validated_data['status']
            else:
                instance.update_status(save_instance=False)

        if 'location_status' in validated_data:
            instance.location_status = validated_data['location_status']

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class VehicleCapacitySerializer(serializers.Serializer):
    # Use SerializerMethodField to return the actual capacity value
    capacity = serializers.SerializerMethodField()

    class Meta:
        model = VehicleInfo
        fields = "__all__"

    def validate_capacity(self, value):
        if not VehicleCapacity.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Selected capacity is invalid.")
        return value

    def get_capacity(self, obj):
        # Assuming 'capacity' is a related field with decimal values like 1.5, 2.5, etc.
        if obj.capacity:
            return {
                "id": obj.id,  # Return the id of the related VehicleCapacity object
                # Add 'T.N' suffix to the capacity value
                "capacity": f"{float(obj.capacity.capacity)} T.N"
            }
        return None


class CreateVehicleCapacitySerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleCapacity
        fields = ['capacity']  # Include fields you want to expose via the API
        extra_kwargs = {
            # Optional: Ensure capacity is at least 0.1
            'capacity': {'validators': [MinValueValidator(0.1)]}
        }

        def validate_capacity(self, value):
            # Check if the capacity already exists in the database
            if VehicleCapacity.objects.filter(capacity=value).exists():
                raise serializers.ValidationError(
                    f"Capacity {value} already exists.")
            return value

    def create(self, validated_data):
        # You can perform custom logic during creation here, if needed
        return super().create(validated_data)


class CreateDocumentSerializer(serializers.ModelSerializer):
    """Serializer for creating multiple VehicleImage instances."""

    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True
    )

    class Meta:
        model = VehicleImage
        fields = ['vehicle', 'images', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        content_type = self.context.get("request").content_type
        if content_type.startswith("multipart/form-data"):
            self.fields['images'] = serializers.ListField(
                child=serializers.ImageField(),
                write_only=True
            )
        elif content_type == 'application/json':
            self.fields['images'] = serializers.ListField(
                child=Base64ImageField(),
                write_only=True
            )
        else:
            raise serializers.ValidationError("Unsupported content type.")

    def validate_images(self, value):
        """Custom validation for multiple images."""
        MAX_SIZE = 5 * 1024 * 1024  # 5MB
        valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf']

        for img in value:
            # Check file size
            if img.size > MAX_SIZE:
                raise serializers.ValidationError(
                    f"Image {img.name} size exceeds the 5MB limit.")
            # Check file type
            if not any(img.name.lower().endswith(ext) for ext in valid_extensions):
                raise serializers.ValidationError(
                    f"Invalid image format for {img.name}. Only JPG, JPEG, and PNG are allowed.")

        return value

    def compress_image(self, img):
        """Compress image by resizing if it's too large."""
        max_width, max_height = 1200, 1200  # Max dimensions (change as needed)
        img_width, img_height = img.size

        # If the image is larger than the max size, resize it
        if img_width > max_width or img_height > max_height:
            img.thumbnail((max_width, max_height))  # Maintain aspect ratio

        return img

    def save_image(self, image):
        """Compress and return the processed image."""
        img = Image.open(image)
        img_format = img.format  # Ensure the correct format for saving
        img = self.compress_image(img)

        # Save the image back into a temporary file buffer
        img_io = io.BytesIO()
        # Adjust quality as needed
        img.save(img_io, format=img_format, quality=85)
        img_io.seek(0)

        # Create a new InMemoryUploadedFile with the compressed image data
        return InMemoryUploadedFile(
            img_io, None, image.name, image.content_type, img_io.getbuffer().nbytes, None
        )

    def create(self, validated_data):
        """Handle creating multiple VehicleImage instances."""
        vehicle = validated_data['vehicle']
        description = validated_data.get('description', None)
        images = validated_data.pop('images')

        vehicle_images = []
        for image in images:
            compressed_image = self.save_image(image)
            vehicle_images.append(
                VehicleImage(vehicle=vehicle, image=compressed_image,
                             description=description)
            )

        # Bulk create all VehicleImage instances
        VehicleImage.objects.bulk_create(vehicle_images)

        image_count = vehicle.images.count()
        if image_count >= 1:
            vehicle.status = vehicle.StatusChoices.IN_PROGRESS
        vehicle.save(update_fields=["status"])
        return vehicle_images


#
class VehicleImageSerializer(serializers.ModelSerializer):
    """Serializer for VehicleImage instances."""
    vehicle = serializers.UUIDField()

    class Meta:
        model = VehicleImage
        # Include relevant fields
        fields = ['id', 'vehicle', 'image', 'description']

    def create(self, validated_data):
        """Handle image upload and update vehicle status."""
        vehicle = validated_data["vehicle"]
        vehicle_image = VehicleImage.objects.create(**validated_data)

        # Update vehicle status dynamically
        vehicle.update_status()

        return vehicle_image

#


class DeleteDocumentSerializer(serializers.Serializer):
    """Serializer for deleting multiple VehicleImage instances and associated files using UUIDs."""
    image_ids = serializers.ListField(
        child=serializers.UUIDField(format='hex_verbose'),
        write_only=True
    )

    def validate_image_ids(self, value):
        """Validate that all provided UUIDs correspond to existing VehicleImage instances."""
        if not value:
            raise serializers.ValidationError(
                "The list of image IDs cannot be empty.")

        # Validate the existence of all images
        invalid_ids = []
        for image_id in value:
            try:
                UUID(str(image_id))  # Ensure it's a valid UUID
            except ValueError:
                invalid_ids.append(image_id)
                continue

            if not VehicleImage.objects.filter(id=image_id).exists():
                invalid_ids.append(image_id)

        if invalid_ids:
            raise serializers.ValidationError(
                f"The following image IDs are invalid or do not exist: {', '.join(map(str, invalid_ids))}"
            )

        return value

    def delete_images(self, user_id):
        """Delete the images based on the validated UUIDs and remove associated files."""
        image_ids = self.validated_data['image_ids']
        deleted_count = 0
        errors = []
        affected_vehicles = set()  # Track vehicles whose images are deleted

        for image_id in image_ids:
            try:
                # Fetch the image instance
                image_instance = VehicleImage.objects.get(id=image_id)

                # Build the file path
                image_path = os.path.join(f"{settings.MEDIA_ROOT}/docs/", str(user_id),
                                          os.path.basename(image_instance.image.name))

                # Delete the file from the file system
                if os.path.exists(image_path):
                    os.remove(image_path)

                # Delete the database record
                image_instance.delete()
                deleted_count += 1
            except VehicleImage.DoesNotExist:
                errors.append(f"Image with ID {image_id} does not exist.")
            except Exception as e:
                errors.append(f"Error deleting image {image_id}: {str(e)}")

            # Update the status of all affected vehicles
        for vehicle in affected_vehicles:
            vehicle.update_status()

        return deleted_count, errors


class VehicleIDField(serializers.IntegerField):
    def to_internal_value(self, data):
        try:
            return UUID(str(data))
        except (ValueError, TypeError, AttributeError):
            raise serializers.ValidationError("Invalid vehicle ID format. Must be a valid UUID.")
        
    def to_representation(self, value):
        return str(value)


class VehicleNotificationCreateSerializer(serializers.ModelSerializer):
    vehicle_id = VehicleIDField(write_only=True, required=True)

    class Meta:
        model = DriverNotification
        fields = [
            'vehicle_id', 'source', 'destination', 'rate', 'weight',
            'date', 'message', 'contact', 'model'
        ]
        extra_kwargs = {
            'message': {'required': True},
        }


class BulkVehicleNotificationSerializer(serializers.Serializer):
    vehicle_ids = serializers.ListField(
        child=VehicleIDField(),
        required=True
    )
    notifications = serializers.ListField(
        child=serializers.DictField()
    )

    def validate(self, data):
        if len(data['notifications']) == 0:
            raise serializers.ValidationError(
                "At least one notification must be provided.")
        return data

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'number']

class GetVehicleNotificationByIdSerializer(serializers.ModelSerializer):
    created_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = DriverNotification
        fields = [
            'id', 'source', 'destination', 'rate', 'weight',
            'date', 'message', 'contact', 'model', 'is_read', 'is_accepted', 
            'created_by', 'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not (instance.is_read and instance.location_read_lock):
            data.pop('message', None)
        return data


class NotificationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverNotification
        fields = ["is_read"]

    def validate_is_read(self, value):
        if value:
            if DriverNotification.objects.filter(
                source=self.instance.source,
                destination=self.instance.destination,
                is_read=True,
                is_accepted=True,
                location_read_lock=True,
            ).exclude(pk=self.instance.pk).exists():
                self.instance.is_accepted = True
                self.instance.save(update_fields=["is_accepted"])
                raise serializers.ValidationError({
                    "vehicle_id": self.instance.vehicle.id,
                    "is_accepted": self.instance.is_accepted,
                    "msg": "This notification is already read by another user."})
            
            else:
                DriverNotification.objects.filter(
                source=self.instance.source,
                destination=self.instance.destination,
                is_read=False,
            ).update(is_accepted=True)

            return value

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleInfo
        fields = "__all__"

class NotificationDetailSerializer(serializers.ModelSerializer):
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = DriverNotification
        fields = [
            'id', 'source', 'destination', 'rate', 'weight',
            'date', 'message', 'contact', 'model', 'is_read', 'is_accepted', 
            'created_by', 'created_at', 'reserved_by', 'is_reserved'
        ]
        depth = 1

    def get_creator_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.name}".strip()
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.rate:
            data['rate'] = float(instance.rate)
        if instance.weight:
            data['weight'] = float(instance.weight)
        if instance.is_read:
            data['vehicle'] = VehicleSerializer(instance.vehicle).data
        return data

class ReadNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverNotification
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        if instance.is_read:
            return super().to_representation(instance)
        return None

class UpdateNotificationByIdSerializer(serializers.ModelSerializer):
    created_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = DriverNotification
        fields = [
            "source", 
            "destination", 
            "rate", 
            "weight", 
            "date", 
            "message", 
            "contact", 
            "model",
            "is_read", 
            "is_accepted",
            "created_by",
            "location_read_lock"
            ]
        extra_kwargs = {
            "source": {"required": False},
            "destination": {"required": False},
            "rate": {"required": False},
            "weight": {"required": False},
            "message": {"required": False},
            "contact": {"required": False},
            "model": {"required": False},
            "is_read": {"required": False},
            "is_accepted": {"required": False},
            "created_by": {"required": False},
            "location_read_lock": {"required": False}
        }

    def update(self, instance, validated_data):
        is_read = validated_data.get("is_read")

        if is_read is False:
            instance.is_read = False
            instance.is_accepted = False
            instance.location_read_lock = False

        for attr, value in validated_data.items():
            if attr != "is_read":
                setattr(instance, attr, value)
        instance.save()
        return super().update(instance, validated_data)