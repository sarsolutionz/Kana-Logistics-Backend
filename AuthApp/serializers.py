from rest_framework import serializers

from AuthApp.models import Driver

class GetAllDriversInfoSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ["id", "name", "email", "number", "is_deleted", "created_at", "updated_at"]

class UpdateDriverInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ["name", "email", "number", "is_deleted"]

    def validate_email(self, value):
        # Optional: ensure no duplicate emails except for current driver
        driver_id = self.instance.id if self.instance else None
        if Driver.objects.exclude(id=driver_id).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_number(self, value):
        # Optional: ensure no duplicate numbers except for current driver
        driver_id = self.instance.id if self.instance else None
        if Driver.objects.exclude(id=driver_id).filter(number=value).exists():
            raise serializers.ValidationError("This number is already in use.")
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class DriverDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['id', "name", "email", "number", "is_deleted", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        