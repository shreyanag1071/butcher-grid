from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Avg

from core.permissions import IsOwnerOrRegulator, IsRegulatoryStaff
from core.models import User
from .models import WasteDisposalLog, EnvironmentalReading
from .serializers import WasteDisposalLogSerializer, EnvironmentalReadingSerializer
from .tasks import score_waste_anomaly


class WasteDisposalLogViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrRegulator]
    serializer_class = WasteDisposalLogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["waste_type", "disposal_method", "is_anomaly", "facility"]
    ordering_fields = ["logged_at", "quantity_kg", "anomaly_score"]

    def get_queryset(self):
        user = self.request.user
        if user.role in (User.Role.REGULATOR, User.Role.ENVIRONMENTAL_AGENCY):
            return WasteDisposalLog.objects.select_related("facility", "logged_by").all()
        return WasteDisposalLog.objects.select_related("facility", "logged_by").filter(
            facility__owner=user
        )

    def perform_create(self, serializer):
        log = serializer.save()
        score_waste_anomaly.delay(str(log.id))

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Aggregated waste summary per facility for the requesting user."""
        qs = self.get_queryset()
        summary = (
            qs.values("facility__name", "waste_type")
            .annotate(total_kg=Sum("quantity_kg"), avg_anomaly=Avg("anomaly_score"))
            .order_by("facility__name", "waste_type")
        )
        return Response(list(summary))

    @action(detail=False, methods=["get"])
    def anomalies(self, request):
        """Return only anomalous waste logs."""
        qs = self.get_queryset().filter(is_anomaly=True).order_by("-anomaly_score")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class EnvironmentalReadingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrRegulator]
    serializer_class = EnvironmentalReadingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["reading_type", "facility", "sensor_id"]
    ordering_fields = ["recorded_at", "nitrate_ppm", "ph_level"]

    def get_queryset(self):
        user = self.request.user
        if user.role in (User.Role.REGULATOR, User.Role.ENVIRONMENTAL_AGENCY):
            return EnvironmentalReading.objects.select_related("facility").all()
        return EnvironmentalReading.objects.select_related("facility").filter(
            facility__owner=user
        )

    @action(detail=False, methods=["get"])
    def contaminated(self, request):
        """Return readings that exceed safe thresholds."""
        from django.db.models import Q
        qs = self.get_queryset().filter(
            Q(ph_level__lt=6.0) | Q(ph_level__gt=8.5) |
            Q(nitrate_ppm__gt=50) |
            Q(coliform_cfu__gt=100)
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
