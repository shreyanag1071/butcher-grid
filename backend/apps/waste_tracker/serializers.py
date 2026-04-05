# serializers.py
from rest_framework import serializers
from .models import WasteDisposalLog, EnvironmentalReading


class WasteDisposalLogSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    logged_by_name = serializers.CharField(source="logged_by.username", read_only=True)

    class Meta:
        model = WasteDisposalLog
        fields = [
            "id", "facility", "facility_name", "waste_type", "quantity_kg",
            "disposal_method", "disposal_partner", "logged_by", "logged_by_name",
            "logged_at", "anomaly_score", "is_anomaly", "notes", "created_at",
        ]
        read_only_fields = ["id", "anomaly_score", "is_anomaly", "logged_by", "created_at"]

    def create(self, validated_data):
        validated_data["logged_by"] = self.context["request"].user
        return super().create(validated_data)


class EnvironmentalReadingSerializer(serializers.ModelSerializer):
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    contamination_flag = serializers.BooleanField(read_only=True)

    class Meta:
        model = EnvironmentalReading
        fields = [
            "id", "facility", "facility_name", "reading_type",
            "ph_level", "nitrate_ppm", "phosphate_ppm", "coliform_cfu",
            "heavy_metal_ppb", "recorded_by", "recorded_at", "sensor_id",
            "latitude", "longitude", "contamination_flag",
        ]
        read_only_fields = ["id", "recorded_by"]

    def create(self, validated_data):
        validated_data["recorded_by"] = self.context["request"].user
        return super().create(validated_data)
