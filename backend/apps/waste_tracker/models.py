from django.db import models
from django.utils import timezone
import uuid


class WasteDisposalLog(models.Model):
    """Record of waste generated and disposal method used."""

    class WasteType(models.TextChoices):
        SOLID_ORGANIC = "solid_organic", "Solid Organic"
        LIQUID_EFFLUENT = "liquid_effluent", "Liquid Effluent"
        BLOOD = "blood", "Blood"
        BONE_MEAL = "bone_meal", "Bone Meal"
        CHEMICAL = "chemical", "Chemical"

    class DisposalMethod(models.TextChoices):
        BIOGAS = "biogas", "Biogas Plant"
        COMPOSTING = "composting", "Composting"
        INCINERATION = "incineration", "Incineration"
        SEWER = "sewer", "Municipal Sewer"
        LAND_FILL = "landfill", "Landfill"
        THIRD_PARTY = "third_party", "Third-Party Handler"
        UNTREATED = "untreated", "Untreated Discharge"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(
        "core.Facility", on_delete=models.CASCADE, related_name="waste_logs"
    )
    waste_type = models.CharField(max_length=20, choices=WasteType.choices)
    quantity_kg = models.FloatField()
    disposal_method = models.CharField(max_length=20, choices=DisposalMethod.choices)
    disposal_partner = models.CharField(
        max_length=255, blank=True, help_text="Name of third-party handler if applicable"
    )
    logged_by = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, related_name="waste_logs"
    )
    logged_at = models.DateTimeField(default=timezone.now)
    # ML anomaly detection
    anomaly_score = models.FloatField(default=0.0)
    is_anomaly = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-logged_at"]

    def __str__(self):
        return f"{self.waste_type} — {self.quantity_kg}kg @ {self.facility.name} ({self.logged_at.date()})"


class EnvironmentalReading(models.Model):
    """Soil or water quality reading near a facility."""

    class ReadingType(models.TextChoices):
        SOIL = "soil", "Soil"
        GROUNDWATER = "groundwater", "Groundwater"
        SURFACE_WATER = "surface_water", "Surface Water"
        AIR = "air", "Air"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(
        "core.Facility", on_delete=models.CASCADE, related_name="env_readings"
    )
    reading_type = models.CharField(max_length=20, choices=ReadingType.choices)
    ph_level = models.FloatField(null=True, blank=True)
    nitrate_ppm = models.FloatField(null=True, blank=True)
    phosphate_ppm = models.FloatField(null=True, blank=True)
    coliform_cfu = models.FloatField(null=True, blank=True, help_text="Coliform CFU/100ml")
    heavy_metal_ppb = models.FloatField(null=True, blank=True)
    recorded_by = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, related_name="env_readings"
    )
    recorded_at = models.DateTimeField(default=timezone.now)
    sensor_id = models.CharField(max_length=100, blank=True, help_text="IoT sensor identifier")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.reading_type} reading @ {self.facility.name} ({self.recorded_at.date()})"

    @property
    def contamination_flag(self):
        """Simple rule-based flag before ML scoring."""
        if self.ph_level and not (6.0 <= self.ph_level <= 8.5):
            return True
        if self.nitrate_ppm and self.nitrate_ppm > 50:
            return True
        if self.coliform_cfu and self.coliform_cfu > 100:
            return True
        return False
