from rest_framework import serializers
from .models import User, Facility, AnimalBatch, Alert


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "phone", "organisation"]
        read_only_fields = ["id"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role", "phone", "organisation"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class FacilitySerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.username", read_only=True)
    compliance_status_display = serializers.CharField(
        source="get_compliance_status_display", read_only=True
    )

    class Meta:
        model = Facility
        fields = [
            "id", "fssai_license", "name", "facility_type", "owner", "owner_name",
            "address", "state", "pincode", "latitude", "longitude",
            "animal_capacity", "compliance_status", "compliance_status_display",
            "risk_score", "is_active", "registered_at",
        ]
        read_only_fields = ["id", "risk_score", "compliance_status", "registered_at"]


class AnimalBatchSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source="facility.name", read_only=True)

    class Meta:
        model = AnimalBatch
        fields = [
            "id", "batch_code", "facility", "facility_name", "species",
            "count", "arrival_date", "status", "qr_code", "created_at",
        ]
        read_only_fields = ["id", "qr_code", "created_at"]


class AlertSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source="facility.name", read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id", "facility", "facility_name", "alert_type", "severity",
            "message", "is_resolved", "resolved_by", "resolved_at", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
