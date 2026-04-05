from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    class Role(models.TextChoices):
        FARM_OWNER = "farm_owner", "Farm Owner"
        REGULATOR = "regulator", "Regulator"
        CONSUMER = "consumer", "Consumer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CONSUMER)
    phone = models.CharField(max_length=15, blank=True)
    organisation = models.CharField(max_length=255, blank=True)


class Facility(models.Model):
    class FacilityType(models.TextChoices):
        FARM = "farm", "Farm"
        SLAUGHTERHOUSE = "slaughterhouse", "Slaughterhouse"

    class ComplianceStatus(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        WARNING = "warning", "Warning"
        NON_COMPLIANT = "non_compliant", "Non-Compliant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fssai_license = models.CharField(max_length=14, unique=True)
    name = models.CharField(max_length=255)
    facility_type = models.CharField(max_length=20, choices=FacilityType.choices, default=FacilityType.FARM)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="facilities")
    state = models.CharField(max_length=50, default="Maharashtra")
    address = models.TextField(blank=True)
    animal_capacity = models.PositiveIntegerField(default=500)
    compliance_status = models.CharField(max_length=20, choices=ComplianceStatus.choices, default=ComplianceStatus.COMPLIANT)
    risk_score = models.FloatField(default=0.0)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} [{self.fssai_license}]"


class AnimalBatch(models.Model):
    class Species(models.TextChoices):
        CHICKEN = "chicken", "Chicken"
        GOAT = "goat", "Goat"
        CATTLE = "cattle", "Cattle"
        PIG = "pig", "Pig"

    class BatchStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        PROCESSED = "processed", "Processed"
        QUARANTINE = "quarantine", "Quarantine"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_code = models.CharField(max_length=50, unique=True)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="batches")
    species = models.CharField(max_length=20, choices=Species.choices)
    count = models.PositiveIntegerField()
    arrival_date = models.DateField()
    status = models.CharField(max_length=20, choices=BatchStatus.choices, default=BatchStatus.ACTIVE)
    qr_code = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.qr_code = f"BG-{str(self.id)[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.batch_code


class MedicationLog(models.Model):
    class MedicationType(models.TextChoices):
        ANTIBIOTIC = "antibiotic", "Antibiotic"
        HORMONE = "hormone", "Hormone"
        VACCINE = "vaccine", "Vaccine"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(AnimalBatch, on_delete=models.CASCADE, related_name="medications")
    medication_name = models.CharField(max_length=255)
    medication_type = models.CharField(max_length=20, choices=MedicationType.choices)
    dosage_mg = models.FloatField()
    withdrawal_period_days = models.PositiveIntegerField(default=0)
    administered_at = models.DateTimeField(auto_now_add=True)
    risk_score = models.FloatField(default=0.0)
    risk_flag = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.medication_name} → {self.batch.batch_code}"


class WasteLog(models.Model):
    class WasteType(models.TextChoices):
        SOLID = "solid", "Solid Organic"
        LIQUID = "liquid", "Liquid Effluent"
        BLOOD = "blood", "Blood"
        CHEMICAL = "chemical", "Chemical"

    class DisposalMethod(models.TextChoices):
        BIOGAS = "biogas", "Biogas Plant"
        COMPOSTING = "composting", "Composting"
        SEWER = "sewer", "Municipal Sewer"
        UNTREATED = "untreated", "Untreated Discharge"
        THIRD_PARTY = "third_party", "Third-Party Handler"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="waste_logs")
    waste_type = models.CharField(max_length=20, choices=WasteType.choices)
    quantity_kg = models.FloatField()
    disposal_method = models.CharField(max_length=20, choices=DisposalMethod.choices)
    anomaly_score = models.FloatField(default=0.0)
    is_anomaly = models.BooleanField(default=False)
    logged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.waste_type} @ {self.facility.name}"


class Alert(models.Model):
    class AlertType(models.TextChoices):
        ANTIBIOTIC_OVERUSE = "antibiotic_overuse", "Antibiotic Overuse"
        HORMONE_FLAG = "hormone_flag", "Hormone Flag"
        WASTE_ANOMALY = "waste_anomaly", "Waste Anomaly"
        COMPLIANCE_BREACH = "compliance_breach", "Compliance Breach"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="alerts")
    alert_type = models.CharField(max_length=30, choices=AlertType.choices)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.severity}] {self.alert_type} @ {self.facility.name}"
