from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """Extended user model with role-based access."""

    class Role(models.TextChoices):
        FARM_OWNER = "farm_owner", "Farm Owner"
        SLAUGHTERHOUSE = "slaughterhouse", "Slaughterhouse Operator"
        REGULATOR = "regulator", "Regulator"
        CONSUMER = "consumer", "Consumer"
        ENVIRONMENTAL_AGENCY = "env_agency", "Environmental Agency"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CONSUMER)
    phone = models.CharField(max_length=15, blank=True)
    organisation = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class State(models.TextChoices):
    ANDHRA_PRADESH = "AP", "Andhra Pradesh"
    KARNATAKA = "KA", "Karnataka"
    KERALA = "KL", "Kerala"
    MAHARASHTRA = "MH", "Maharashtra"
    TAMIL_NADU = "TN", "Tamil Nadu"
    TELANGANA = "TS", "Telangana"
    UTTAR_PRADESH = "UP", "Uttar Pradesh"
    WEST_BENGAL = "WB", "West Bengal"
    OTHER = "OT", "Other"


class Facility(models.Model):
    """A registered farm or slaughterhouse."""

    class FacilityType(models.TextChoices):
        FARM = "farm", "Farm"
        SLAUGHTERHOUSE = "slaughterhouse", "Slaughterhouse"
        INTEGRATED = "integrated", "Integrated (Farm + Slaughter)"

    class ComplianceStatus(models.TextChoices):
        COMPLIANT = "compliant", "Compliant"
        WARNING = "warning", "Warning"
        NON_COMPLIANT = "non_compliant", "Non-Compliant"
        UNDER_REVIEW = "under_review", "Under Review"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fssai_license = models.CharField(max_length=14, unique=True)
    name = models.CharField(max_length=255)
    facility_type = models.CharField(max_length=20, choices=FacilityType.choices)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="facilities")
    address = models.TextField()
    state = models.CharField(max_length=2, choices=State.choices)
    pincode = models.CharField(max_length=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    animal_capacity = models.PositiveIntegerField(default=0)
    compliance_status = models.CharField(
        max_length=20,
        choices=ComplianceStatus.choices,
        default=ComplianceStatus.UNDER_REVIEW,
    )
    risk_score = models.FloatField(default=0.0, help_text="0.0 (low) to 1.0 (high risk)")
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "facilities"
        ordering = ["-registered_at"]

    def __str__(self):
        return f"{self.name} [{self.fssai_license}]"


class AnimalBatch(models.Model):
    """A batch of animals at a facility."""

    class Species(models.TextChoices):
        CHICKEN = "chicken", "Chicken"
        GOAT = "goat", "Goat"
        CATTLE = "cattle", "Cattle"
        PIG = "pig", "Pig"
        FISH = "fish", "Fish"

    class BatchStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        PROCESSED = "processed", "Processed"
        QUARANTINE = "quarantine", "Quarantine"
        DECEASED = "deceased", "Deceased"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_code = models.CharField(max_length=50, unique=True)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="batches")
    species = models.CharField(max_length=20, choices=Species.choices)
    count = models.PositiveIntegerField()
    arrival_date = models.DateField()
    status = models.CharField(max_length=20, choices=BatchStatus.choices, default=BatchStatus.ACTIVE)
    qr_code = models.CharField(max_length=255, blank=True, help_text="QR token for consumer scan")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-arrival_date"]

    def __str__(self):
        return f"{self.batch_code} — {self.species} @ {self.facility.name}"


class Alert(models.Model):
    """System-generated alert for overuse, anomaly, or compliance breach."""

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
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="resolved_alerts"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.alert_type} @ {self.facility.name}"
