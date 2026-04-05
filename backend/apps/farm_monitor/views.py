from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.conf import settings

from core.permissions import IsFarmOwner, IsOwnerOrRegulator
from core.models import AnimalBatch, Alert
from .models import MedicationLog, HealthRecord, HormoneTest
from .serializers import (
    MedicationLogSerializer,
    MedicationLogCreateSerializer,
    HealthRecordSerializer,
    HormoneTestSerializer,
)
from .tasks import run_medication_risk_score


class MedicationLogViewSet(viewsets.ModelViewSet):
    """
    CRUD for medication logs. Farm owners see their own facility logs only.
    Regulators see all.
    """

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["medication_type", "risk_flag", "batch__facility"]
    ordering_fields = ["administered_at", "risk_score"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsOwnerOrRegulator()]
        return [IsFarmOwner()]

    def get_queryset(self):
        user = self.request.user
        from core.models import User
        if user.role in (User.Role.REGULATOR, User.Role.ENVIRONMENTAL_AGENCY):
            return MedicationLog.objects.select_related("batch__facility", "administered_by").all()
        return MedicationLog.objects.select_related("batch__facility", "administered_by").filter(
            batch__facility__owner=user
        )

    def get_serializer_class(self):
        if self.action == "create":
            return MedicationLogCreateSerializer
        return MedicationLogSerializer

    def perform_create(self, serializer):
        log = serializer.save()
        # Trigger async ML risk scoring
        run_medication_risk_score.delay(str(log.id))

    @action(detail=False, methods=["get"])
    def overuse_alerts(self, request):
        """Return batches with antibiotics administered more than threshold days in a row."""
        threshold = settings.ANTIBIOTIC_OVERUSE_THRESHOLD_DAYS
        from django.db.models import Count
        from django.utils.timezone import now
        cutoff = now() - timezone.timedelta(days=threshold)
        flagged = (
            MedicationLog.objects.filter(
                medication_type=MedicationLog.MedicationType.ANTIBIOTIC,
                administered_at__gte=cutoff,
                batch__facility__owner=request.user,
            )
            .values("batch__batch_code", "batch__facility__name")
            .annotate(log_count=Count("id"))
            .filter(log_count__gte=threshold)
        )
        return Response(list(flagged))

    @action(detail=True, methods=["post"])
    def rescore(self, request, pk=None):
        """Manually trigger ML risk rescoring for a medication log."""
        log = self.get_object()
        run_medication_risk_score.delay(str(log.id))
        return Response({"detail": "Risk scoring queued."}, status=status.HTTP_202_ACCEPTED)


class HealthRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrRegulator]
    serializer_class = HealthRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "batch__facility"]
    ordering_fields = ["recorded_at"]

    def get_queryset(self):
        user = self.request.user
        from core.models import User
        if user.role in (User.Role.REGULATOR, User.Role.ENVIRONMENTAL_AGENCY):
            return HealthRecord.objects.select_related("batch", "recorded_by").all()
        return HealthRecord.objects.select_related("batch", "recorded_by").filter(
            batch__facility__owner=user
        )

    @action(detail=False, methods=["get"])
    def mortality_summary(self, request):
        """Summarise mortality counts per facility for the requesting owner."""
        from django.db.models import Sum
        summary = (
            HealthRecord.objects.filter(batch__facility__owner=request.user)
            .values("batch__facility__name")
            .annotate(total_mortality=Sum("mortality_count"))
            .order_by("-total_mortality")
        )
        return Response(list(summary))


class HormoneTestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrRegulator]
    serializer_class = HormoneTestSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["result", "hormone_name", "batch__facility"]
    ordering_fields = ["tested_at", "measured_level"]

    def get_queryset(self):
        user = self.request.user
        from core.models import User
        if user.role in (User.Role.REGULATOR, User.Role.ENVIRONMENTAL_AGENCY):
            return HormoneTest.objects.select_related("batch__facility").all()
        return HormoneTest.objects.select_related("batch__facility").filter(
            batch__facility__owner=user
        )

    @action(detail=False, methods=["get"])
    def failures(self, request):
        """Return all failed hormone tests for regulatory view."""
        qs = self.get_queryset().filter(result=HormoneTest.TestResult.FAIL)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
