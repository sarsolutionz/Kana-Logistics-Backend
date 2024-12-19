import re
import logging
from rest_framework import serializers
from .models import VehicleInfo, VehicleCapacity
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator

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
    address = serializers.CharField(max_length=255)
    vehicle_type = serializers.ChoiceField(
        choices=[('open', 'Open'), ('close', 'Close')])
    capacity = serializers.DecimalField(max_digits=4, decimal_places=1)

    class Meta:
        model = VehicleInfo
        fields = ['model', 'name', 'number', 'address',
                  'vehicle_type', 'vehicle_number', 'capacity']

    def validate(self, attrs):
        try:
            # Validate required fields
            required_fields = ['model', 'capacity', 'name',
                               'number', 'vehicle_number', 'vehicle_type']
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
            instance.model = validated_data.get('model', instance.model)
            instance.name = validated_data.get('name', instance.name)
            instance.number = validated_data.get('number', instance.number)
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
        return float(obj.capacity.capacity)  # Assuming capacity is a related model


class UpdateVehicleInfoByIDSerializer(serializers.ModelSerializer):
    capacity = serializers.DecimalField(
        source='capacity.capacity', max_digits=4, decimal_places=1)

    class Meta:
        model = VehicleInfo
        fields = ['id', 'model', 'name', 'number', 'address',
                  'vehicle_type', 'vehicle_number', 'capacity']

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

    def update(self, instance, validated_data):
        """
        Update the fields of the VehicleInfo model.
        """
        capacity_data = validated_data.pop('capacity', None)

        # Handle the capacity update if it exists
        if capacity_data:
            capacity_value = capacity_data['capacity']
            capacity_obj, created = VehicleCapacity.objects.get_or_create(
                capacity=capacity_value)
            instance.capacity = capacity_obj

        # Update other fields
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
