from rest_framework import serializers
from django.utils import timezone
from .models import MedicationLog, HealthRecord, HormoneTest


class MedicationLogSerializer(serializers.ModelSerializer):
    batch_code = serializers.CharField(source="batch.batch_code", read_only=True)
    administered_by_name = serializers.CharField(
        source="administered_by.username", read_only=True
    )
    withdrawal_clear_date = serializers.DateField(read_only=True)
    days_until_clear = serializers.SerializerMethodField()

    class Meta:
        model = MedicationLog
        fields = [
            "id", "batch", "batch_code", "medication_name", "medication_type",
            "dosage_mg", "route", "administered_by", "administered_by_name",
            "administered_at", "withdrawal_period_days", "withdrawal_clear_date",
            "days_until_clear", "notes", "risk_flag", "risk_score", "created_at",
        ]
        read_only_fields = ["id", "risk_flag", "risk_score", "created_at"]

    def get_days_until_clear(self, obj):
        remaining = (obj.withdrawal_clear_date - timezone.now().date()).days
        return max(remaining, 0)


class MedicationLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationLog
        fields = [
            "batch", "medication_name", "medication_type", "dosage_mg",
            "route", "administered_at", "withdrawal_period_days", "notes",
        ]

    def validate(self, data):
        # Ensure batch belongs to a facility owned by the requesting user
        request = self.context.get("request")
        if request and data.get("batch"):
            facility = data["batch"].facility
            if facility.owner != request.user:
                raise serializers.ValidationError(
                    "You can only log medications for your own facility's batches."
                )
        return data

    def create(self, validated_data):
        validated_data["administered_by"] = self.context["request"].user
        return super().create(validated_data)


class HealthRecordSerializer(serializers.ModelSerializer):
    batch_code = serializers.CharField(source="batch.batch_code", read_only=True)
    recorded_by_name = serializers.CharField(source="recorded_by.username", read_only=True)

    class Meta:
        model = HealthRecord
        fields = [
            "id", "batch", "batch_code", "recorded_by", "recorded_by_name",
            "status", "average_weight_kg", "mortality_count", "symptoms",
            "recorded_at", "notes",
        ]
        read_only_fields = ["id", "recorded_by"]

    def create(self, validated_data):
        validated_data["recorded_by"] = self.context["request"].user
        return super().create(validated_data)


class HormoneTestSerializer(serializers.ModelSerializer):
    batch_code = serializers.CharField(source="batch.batch_code", read_only=True)
    exceeds_limit = serializers.SerializerMethodField()

    class Meta:
        model = HormoneTest
        fields = [
            "id", "batch", "batch_code", "lab_name", "hormone_name",
            "measured_level", "permissible_limit", "result", "tested_at",
            "certificate_url", "exceeds_limit", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_exceeds_limit(self, obj):
        return obj.measured_level > obj.permissible_limit
