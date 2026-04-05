from django.db import models
from django.utils import timezone
import uuid


class MedicationLog(models.Model):
    """Record of antibiotic or hormone administration to a batch."""

    class MedicationType(models.TextChoices):
        ANTIBIOTIC = "antibiotic", "Antibiotic"
        HORMONE = "hormone", "Hormone"
        VACCINE = "vaccine", "Vaccine"
        OTHER = "other", "Other"

    class RouteOfAdmin(models.TextChoices):
        ORAL = "oral", "Oral"
        INJECTION = "injection", "Injection"
        TOPICAL = "topical", "Topical"
        FEED_ADDITIVE = "feed_additive", "Feed Additive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        "core.AnimalBatch", on_delete=models.CASCADE, related_name="medication_logs"
    )
    medication_name = models.CharField(max_length=255)
    medication_type = models.CharField(max_length=20, choices=MedicationType.choices)
    dosage_mg = models.FloatField(help_text="Dosage in milligrams")
    route = models.CharField(max_length=20, choices=RouteOfAdmin.choices)
    administered_by = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, related_name="medication_logs"
    )
    administered_at = models.DateTimeField(default=timezone.now)
    withdrawal_period_days = models.PositiveIntegerField(
        default=0, help_text="Minimum days before slaughter after this medication"
    )
    notes = models.TextField(blank=True)
    # ML inference result
    risk_flag = models.BooleanField(default=False)
    risk_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-administered_at"]

    def __str__(self):
        return f"{self.medication_name} → {self.batch.batch_code} ({self.administered_at.date()})"

    @property
    def withdrawal_clear_date(self):
        return self.administered_at.date() + timezone.timedelta(days=self.withdrawal_period_days)


class HealthRecord(models.Model):
    """Periodic health assessment of an animal batch."""

    class HealthStatus(models.TextChoices):
        HEALTHY = "healthy", "Healthy"
        SICK = "sick", "Sick"
        RECOVERING = "recovering", "Recovering"
        CRITICAL = "critical", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        "core.AnimalBatch", on_delete=models.CASCADE, related_name="health_records"
    )
    recorded_by = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, related_name="health_records"
    )
    status = models.CharField(max_length=20, choices=HealthStatus.choices)
    average_weight_kg = models.FloatField(null=True, blank=True)
    mortality_count = models.PositiveIntegerField(default=0)
    symptoms = models.TextField(blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.batch.batch_code} — {self.status} @ {self.recorded_at.date()}"


class HormoneTest(models.Model):
    """Lab test result for hormone levels in a batch sample."""

    class TestResult(models.TextChoices):
        PASS = "pass", "Pass"
        FAIL = "fail", "Fail"
        PENDING = "pending", "Pending"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        "core.AnimalBatch", on_delete=models.CASCADE, related_name="hormone_tests"
    )
    lab_name = models.CharField(max_length=255)
    hormone_name = models.CharField(max_length=100)
    measured_level = models.FloatField(help_text="Measured level in ppb")
    permissible_limit = models.FloatField(help_text="Regulatory limit in ppb")
    result = models.CharField(max_length=10, choices=TestResult.choices, default=TestResult.PENDING)
    tested_at = models.DateTimeField(default=timezone.now)
    certificate_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tested_at"]

    def __str__(self):
        return f"{self.hormone_name} test — {self.batch.batch_code} [{self.result}]"
