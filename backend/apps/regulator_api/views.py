from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Q
from django.utils import timezone

from core.permissions import IsRegulator, IsRegulatoryStaff
from core.models import Facility, Alert, AnimalBatch, User
from core.serializers import FacilitySerializer, AlertSerializer
from apps.farm_monitor.models import MedicationLog, HormoneTest
from apps.waste_tracker.models import WasteDisposalLog, EnvironmentalReading


class FacilityRegulatoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Full facility visibility for regulators — read-only with
    compliance update actions.
    """
    permission_classes = [IsRegulatoryStaff]
    serializer_class = FacilitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["state", "compliance_status", "facility_type", "is_active"]
    search_fields = ["name", "fssai_license", "owner__username"]
    ordering_fields = ["risk_score", "registered_at", "name"]

    def get_queryset(self):
        return Facility.objects.select_related("owner").all()

    @action(detail=True, methods=["patch"])
    def update_compliance(self, request, pk=None):
        """Allow regulators to manually update a facility's compliance status."""
        facility = self.get_object()
        new_status = request.data.get("compliance_status")
        valid = [c[0] for c in Facility.ComplianceStatus.choices]
        if new_status not in valid:
            return Response(
                {"error": f"Invalid status. Choose from {valid}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        facility.compliance_status = new_status
        facility.save(update_fields=["compliance_status"])
        return Response({"detail": f"Compliance status updated to '{new_status}'."})

    @action(detail=True, methods=["get"])
    def full_audit(self, request, pk=None):
        """
        Aggregate audit trail for a single facility:
        medication logs, hormone tests, waste logs, env readings, alerts.
        """
        facility = self.get_object()
        cutoff = timezone.now() - timezone.timedelta(days=90)

        medication_summary = (
            MedicationLog.objects.filter(batch__facility=facility, created_at__gte=cutoff)
            .values("medication_type")
            .annotate(count=Count("id"), flagged=Count("id", filter=Q(risk_flag=True)))
        )

        hormone_summary = (
            HormoneTest.objects.filter(batch__facility=facility)
            .values("result")
            .annotate(count=Count("id"))
        )

        waste_summary = (
            WasteDisposalLog.objects.filter(facility=facility, logged_at__gte=cutoff)
            .values("disposal_method")
            .annotate(count=Count("id"), anomalies=Count("id", filter=Q(is_anomaly=True)))
        )

        env_flags = EnvironmentalReading.objects.filter(
            facility=facility
        ).filter(
            Q(ph_level__lt=6.0) | Q(ph_level__gt=8.5) |
            Q(nitrate_ppm__gt=50) | Q(coliform_cfu__gt=100)
        ).count()

        open_alerts = Alert.objects.filter(facility=facility, is_resolved=False).count()

        return Response({
            "facility": FacilitySerializer(facility).data,
            "audit_window_days": 90,
            "medication_summary": list(medication_summary),
            "hormone_test_summary": list(hormone_summary),
            "waste_summary": list(waste_summary),
            "environmental_contamination_readings": env_flags,
            "open_alerts": open_alerts,
        })

    @action(detail=False, methods=["get"])
    def high_risk(self, request):
        """Facilities with risk_score above 0.7 — needs immediate attention."""
        qs = self.get_queryset().filter(risk_score__gte=0.7).order_by("-risk_score")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class AlertViewSet(viewsets.ModelViewSet):
    permission_classes = [IsRegulatoryStaff]
    serializer_class = AlertSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["alert_type", "severity", "is_resolved", "facility"]
    ordering_fields = ["created_at", "severity"]

    def get_queryset(self):
        return Alert.objects.select_related("facility", "resolved_by").all()

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        if alert.is_resolved:
            return Response({"detail": "Alert already resolved."}, status=status.HTTP_400_BAD_REQUEST)
        alert.is_resolved = True
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.save(update_fields=["is_resolved", "resolved_by", "resolved_at"])
        return Response({"detail": "Alert resolved."})

    @action(detail=False, methods=["get"])
    def open(self, request):
        qs = self.get_queryset().filter(is_resolved=False).order_by("-created_at")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class NationalDashboardView(APIView):
    """
    High-level national metrics for regulatory dashboard.
    Cached for 15 minutes to avoid heavy DB hits on every poll.
    """
    permission_classes = [IsRegulatoryStaff]

    def get(self, request):
        from django.core.cache import cache
        CACHE_KEY = "national_dashboard_v1"
        cached = cache.get(CACHE_KEY)
        if cached:
            return Response(cached)

        total_facilities = Facility.objects.filter(is_active=True).count()
        compliance_breakdown = dict(
            Facility.objects.values_list("compliance_status")
            .annotate(count=Count("compliance_status"))
            .values_list("compliance_status", "count")
        )
        avg_risk = Facility.objects.aggregate(avg=Avg("risk_score"))["avg"] or 0.0

        open_alerts_by_type = dict(
            Alert.objects.filter(is_resolved=False)
            .values_list("alert_type")
            .annotate(count=Count("alert_type"))
            .values_list("alert_type", "count")
        )

        recent_hormone_failures = HormoneTest.objects.filter(
            result="fail",
            tested_at__gte=timezone.now() - timezone.timedelta(days=30),
        ).count()

        recent_waste_anomalies = WasteDisposalLog.objects.filter(
            is_anomaly=True,
            logged_at__gte=timezone.now() - timezone.timedelta(days=30),
        ).count()

        state_risk = list(
            Facility.objects.values("state")
            .annotate(avg_risk=Avg("risk_score"), count=Count("id"))
            .order_by("-avg_risk")
        )

        data = {
            "total_active_facilities": total_facilities,
            "compliance_breakdown": compliance_breakdown,
            "average_risk_score": round(avg_risk, 3),
            "open_alerts_by_type": open_alerts_by_type,
            "hormone_test_failures_last_30d": recent_hormone_failures,
            "waste_anomalies_last_30d": recent_waste_anomalies,
            "risk_by_state": state_risk,
            "generated_at": timezone.now().isoformat(),
        }

        cache.set(CACHE_KEY, data, timeout=900)
        return Response(data)
