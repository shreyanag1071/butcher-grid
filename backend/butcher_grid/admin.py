from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Facility, AnimalBatch, MedicationLog, WasteLog, Alert

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "organisation"]
    list_filter = ["role"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Butcher Grid", {"fields": ("role", "phone", "organisation")}),
    )

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ["name", "fssai_license", "state", "compliance_status", "risk_score"]
    list_filter = ["compliance_status", "state"]

@admin.register(AnimalBatch)
class AnimalBatchAdmin(admin.ModelAdmin):
    list_display = ["batch_code", "facility", "species", "count", "status", "qr_code"]

@admin.register(MedicationLog)
class MedicationLogAdmin(admin.ModelAdmin):
    list_display = ["medication_name", "medication_type", "batch", "risk_score", "risk_flag"]
    list_filter = ["risk_flag", "medication_type"]

@admin.register(WasteLog)
class WasteLogAdmin(admin.ModelAdmin):
    list_display = ["facility", "waste_type", "quantity_kg", "disposal_method", "is_anomaly"]
    list_filter = ["is_anomaly", "disposal_method"]

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["facility", "alert_type", "severity", "is_resolved", "created_at"]
    list_filter = ["severity", "is_resolved", "alert_type"]
