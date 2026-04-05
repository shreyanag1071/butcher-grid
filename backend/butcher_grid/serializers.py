from rest_framework import serializers
from .models import User, Facility, AnimalBatch, MedicationLog, WasteLog, Alert


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role", "phone", "organisation"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "phone", "organisation"]


class FacilitySerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Facility
        fields = [
            "id", "fssai_license", "name", "facility_type", "owner", "owner_name",
            "state", "address", "animal_capacity", "compliance_status",
            "risk_score", "registered_at",
        ]
        read_only_fields = ["id", "risk_score", "compliance_status", "registered_at", "owner"]


class AnimalBatchSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source="facility.name", read_only=True)

    class Meta:
        model = AnimalBatch
        fields = [
            "id", "batch_code", "facility", "facility_name", "species",
            "count", "arrival_date", "status", "qr_code", "created_at",
        ]
        read_only_fields = ["id", "qr_code", "created_at"]


class MedicationLogSerializer(serializers.ModelSerializer):
    batch_code = serializers.CharField(source="batch.batch_code", read_only=True)
    species = serializers.CharField(source="batch.species", read_only=True)
    facility_name = serializers.CharField(source="batch.facility.name", read_only=True)

    class Meta:
        model = MedicationLog
        fields = [
            "id", "batch", "batch_code", "species", "facility_name",
            "medication_name", "medication_type", "dosage_mg",
            "withdrawal_period_days", "administered_at",
            "risk_score", "risk_flag", "notes",
        ]
        read_only_fields = ["id", "risk_score", "risk_flag", "administered_at"]


class WasteLogSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source="facility.name", read_only=True)

    class Meta:
        model = WasteLog
        fields = [
            "id", "facility", "facility_name", "waste_type", "quantity_kg",
            "disposal_method", "anomaly_score", "is_anomaly", "logged_at",
        ]
        read_only_fields = ["id", "anomaly_score", "is_anomaly", "logged_at"]


class AlertSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source="facility.name", read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id", "facility", "facility_name", "alert_type",
            "severity", "message", "is_resolved", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
