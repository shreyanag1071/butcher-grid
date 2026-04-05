from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Facility, AnimalBatch, Alert


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "organisation", "is_active"]
    list_filter = ["role", "is_active"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Butcher Grid", {"fields": ("role", "phone", "organisation")}),
    )


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ["name", "fssai_license", "facility_type", "state", "compliance_status", "risk_score", "is_active"]
    list_filter = ["facility_type", "state", "compliance_status", "is_active"]
    search_fields = ["name", "fssai_license", "owner__username"]
    readonly_fields = ["id", "registered_at", "updated_at"]


@admin.register(AnimalBatch)
class AnimalBatchAdmin(admin.ModelAdmin):
    list_display = ["batch_code", "facility", "species", "count", "arrival_date", "status"]
    list_filter = ["species", "status"]
    search_fields = ["batch_code", "facility__name"]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["facility", "alert_type", "severity", "is_resolved", "created_at"]
    list_filter = ["alert_type", "severity", "is_resolved"]
    search_fields = ["facility__name", "message"]
    readonly_fields = ["id", "created_at"]
