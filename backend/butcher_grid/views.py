from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, Avg

from .models import User, Facility, AnimalBatch, MedicationLog, WasteLog, Alert
from .serializers import (
    RegisterSerializer, UserSerializer, FacilitySerializer,
    AnimalBatchSerializer, MedicationLogSerializer, WasteLogSerializer, AlertSerializer,
)
from .ml_scorer import score_medication, score_waste, compute_facility_risk


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class ProfileView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ── Facilities ────────────────────────────────────────────────────────────────

class FacilityListCreateView(APIView):
    def get(self, request):
        if request.user.role == User.Role.REGULATOR:
            facilities = Facility.objects.all()
        else:
            facilities = Facility.objects.filter(owner=request.user)
        return Response(FacilitySerializer(facilities, many=True).data)

    def post(self, request):
        serializer = FacilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FacilityDetailView(APIView):
    def get_object(self, pk, user):
        try:
            f = Facility.objects.get(pk=pk)
            if user.role != User.Role.REGULATOR and f.owner != user:
                return None
            return f
        except Facility.DoesNotExist:
            return None

    def get(self, request, pk):
        facility = self.get_object(pk, request.user)
        if not facility:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(FacilitySerializer(facility).data)


# ── Animal Batches ────────────────────────────────────────────────────────────

class BatchListCreateView(APIView):
    def get(self, request):
        if request.user.role == User.Role.REGULATOR:
            batches = AnimalBatch.objects.select_related("facility").all()
        else:
            batches = AnimalBatch.objects.select_related("facility").filter(
                facility__owner=request.user
            )
        return Response(AnimalBatchSerializer(batches, many=True).data)

    def post(self, request):
        serializer = AnimalBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ── Medications ───────────────────────────────────────────────────────────────

class MedicationListCreateView(APIView):
    def get(self, request):
        if request.user.role == User.Role.REGULATOR:
            logs = MedicationLog.objects.select_related("batch__facility").all()
        else:
            logs = MedicationLog.objects.select_related("batch__facility").filter(
                batch__facility__owner=request.user
            )
        return Response(MedicationLogSerializer(logs, many=True).data)

    def post(self, request):
        serializer = MedicationLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        batch_id = request.data.get("batch")
        try:
            batch = AnimalBatch.objects.get(pk=batch_id)
        except AnimalBatch.DoesNotExist:
            return Response({"error": "Batch not found."}, status=404)

        # Count recent antibiotics for this batch (last 7 days)
        cutoff = timezone.now() - timezone.timedelta(days=7)
        recent_count = MedicationLog.objects.filter(
            batch=batch,
            medication_type="antibiotic",
            administered_at__gte=cutoff,
        ).count()

        # Run ML scoring synchronously — no Celery needed
        result = score_medication(
            medication_name=request.data.get("medication_name", ""),
            medication_type=request.data.get("medication_type", ""),
            dosage_mg=float(request.data.get("dosage_mg", 0)),
            withdrawal_period_days=int(request.data.get("withdrawal_period_days", 0)),
            recent_antibiotic_count=recent_count,
        )

        log = serializer.save(
            risk_score=result["risk_score"],
            risk_flag=result["risk_flag"],
        )

        # Auto-create alert if flagged
        if result["risk_flag"]:
            Alert.objects.create(
                facility=batch.facility,
                alert_type=Alert.AlertType.ANTIBIOTIC_OVERUSE
                if log.medication_type == "antibiotic"
                else Alert.AlertType.HORMONE_FLAG,
                severity=result["severity"],
                message=f"{log.medication_name} flagged on batch {batch.batch_code}. "
                        f"Risk score: {result['risk_score']}. Reasons: {'; '.join(result['reasons'])}.",
            )
            _refresh_facility_risk(batch.facility)

        return Response({
            **MedicationLogSerializer(log).data,
            "ml_result": result,
        }, status=status.HTTP_201_CREATED)


# ── Waste ─────────────────────────────────────────────────────────────────────

class WasteListCreateView(APIView):
    def get(self, request):
        if request.user.role == User.Role.REGULATOR:
            logs = WasteLog.objects.select_related("facility").all()
        else:
            logs = WasteLog.objects.select_related("facility").filter(
                facility__owner=request.user
            )
        return Response(WasteLogSerializer(logs, many=True).data)

    def post(self, request):
        serializer = WasteLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        facility_id = request.data.get("facility")
        try:
            facility = Facility.objects.get(pk=facility_id)
        except Facility.DoesNotExist:
            return Response({"error": "Facility not found."}, status=404)

        recent_anomalies = WasteLog.objects.filter(
            facility=facility,
            is_anomaly=True,
            logged_at__gte=timezone.now() - timezone.timedelta(days=30),
        ).count()

        result = score_waste(
            waste_type=request.data.get("waste_type", ""),
            quantity_kg=float(request.data.get("quantity_kg", 0)),
            disposal_method=request.data.get("disposal_method", ""),
            recent_anomaly_count=recent_anomalies,
        )

        log = serializer.save(
            anomaly_score=result["anomaly_score"],
            is_anomaly=result["is_anomaly"],
        )

        if result["is_anomaly"]:
            Alert.objects.create(
                facility=facility,
                alert_type=Alert.AlertType.WASTE_ANOMALY,
                severity=result["severity"],
                message=f"Waste anomaly at {facility.name}: {log.quantity_kg}kg of "
                        f"{log.waste_type} via {log.disposal_method}. "
                        f"Score: {result['anomaly_score']}. Reasons: {'; '.join(result['reasons'])}.",
            )
            _refresh_facility_risk(facility)

        return Response({
            **WasteLogSerializer(log).data,
            "ml_result": result,
        }, status=status.HTTP_201_CREATED)


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertListView(APIView):
    def get(self, request):
        if request.user.role == User.Role.REGULATOR:
            alerts = Alert.objects.select_related("facility").all()
        else:
            alerts = Alert.objects.select_related("facility").filter(
                facility__owner=request.user
            )
        return Response(AlertSerializer(alerts, many=True).data)


class AlertResolveView(APIView):
    def post(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response(status=404)
        alert.is_resolved = True
        alert.save()
        return Response({"detail": "Alert resolved."})


# ── Consumer QR Scan (public) ─────────────────────────────────────────────────

class QRScanView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, qr_code):
        try:
            batch = AnimalBatch.objects.select_related("facility").get(qr_code=qr_code)
        except AnimalBatch.DoesNotExist:
            return Response({"error": "Product not found."}, status=404)

        facility = batch.facility
        meds = MedicationLog.objects.filter(batch=batch)
        antibiotic_count = meds.filter(medication_type="antibiotic").count()
        hormone_count = meds.filter(medication_type="hormone").count()
        any_flagged = meds.filter(risk_flag=True).exists()

        overall_safe = (
            not any_flagged
            and facility.compliance_status == "compliant"
            and facility.risk_score < 0.5
        )

        return Response({
            "batch_code": batch.batch_code,
            "species": batch.get_species_display(),
            "arrival_date": batch.arrival_date,
            "facility": {
                "name": facility.name,
                "state": facility.state,
                "fssai_license": facility.fssai_license,
                "compliance_status": facility.compliance_status,
                "risk_score": round(facility.risk_score, 2),
            },
            "medications": {
                "antibiotic_administrations": antibiotic_count,
                "hormone_administrations": hormone_count,
                "any_risk_flagged": any_flagged,
            },
            "overall_safe": overall_safe,
            "safety_label": "✅ Safe to consume" if overall_safe else "⚠️ Flagged — review recommended",
        })


# ── Regulator Dashboard ───────────────────────────────────────────────────────

class DashboardView(APIView):
    def get(self, request):
        facilities = Facility.objects.all()
        total = facilities.count()
        compliance_breakdown = {
            "compliant": facilities.filter(compliance_status="compliant").count(),
            "warning": facilities.filter(compliance_status="warning").count(),
            "non_compliant": facilities.filter(compliance_status="non_compliant").count(),
        }
        avg_risk = facilities.aggregate(avg=Avg("risk_score"))["avg"] or 0.0
        open_alerts = Alert.objects.filter(is_resolved=False).count()
        critical_alerts = Alert.objects.filter(is_resolved=False, severity="critical").count()

        flagged_meds = MedicationLog.objects.filter(risk_flag=True).count()
        waste_anomalies = WasteLog.objects.filter(is_anomaly=True).count()

        high_risk_facilities = FacilitySerializer(
            facilities.filter(risk_score__gte=0.6).order_by("-risk_score")[:5],
            many=True,
        ).data

        recent_alerts = AlertSerializer(
            Alert.objects.filter(is_resolved=False).order_by("-created_at")[:10],
            many=True,
        ).data

        return Response({
            "total_facilities": total,
            "compliance_breakdown": compliance_breakdown,
            "average_risk_score": round(avg_risk, 3),
            "open_alerts": open_alerts,
            "critical_alerts": critical_alerts,
            "flagged_medication_logs": flagged_meds,
            "waste_anomalies": waste_anomalies,
            "high_risk_facilities": high_risk_facilities,
            "recent_alerts": recent_alerts,
        })


# ── Helper ────────────────────────────────────────────────────────────────────

def _refresh_facility_risk(facility):
    """Recompute and save a facility's composite risk score."""
    flagged_meds = MedicationLog.objects.filter(
        batch__facility=facility, risk_flag=True
    ).count()
    waste_anomalies = WasteLog.objects.filter(
        facility=facility, is_anomaly=True
    ).count()
    open_alerts = Alert.objects.filter(
        facility=facility, is_resolved=False
    ).count()

    new_score = compute_facility_risk(flagged_meds, waste_anomalies, open_alerts)

    if new_score >= 0.75:
        compliance = Facility.ComplianceStatus.NON_COMPLIANT
    elif new_score >= 0.45:
        compliance = Facility.ComplianceStatus.WARNING
    else:
        compliance = Facility.ComplianceStatus.COMPLIANT

    Facility.objects.filter(pk=facility.pk).update(
        risk_score=new_score,
        compliance_status=compliance,
    )
