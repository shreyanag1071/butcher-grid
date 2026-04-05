from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from core.models import AnimalBatch, Facility
from core.serializers import AnimalBatchSerializer, FacilitySerializer
from apps.farm_monitor.models import MedicationLog, HormoneTest
from apps.waste_tracker.models import WasteDisposalLog


class BatchTraceView(APIView):
    """
    Public endpoint. Consumers scan a QR code to get the full traceability
    summary for a batch — no login required.
    """
    permission_classes = [AllowAny]

    def get(self, request, qr_code):
        try:
            batch = AnimalBatch.objects.select_related("facility").get(qr_code=qr_code)
        except AnimalBatch.DoesNotExist:
            return Response(
                {"error": "Product not found. Please verify the QR code."},
                status=status.HTTP_404_NOT_FOUND,
            )

        facility = batch.facility

        # Medication summary (no sensitive details exposed)
        meds = MedicationLog.objects.filter(batch=batch)
        antibiotic_count = meds.filter(medication_type="antibiotic").count()
        hormone_count = meds.filter(medication_type="hormone").count()
        any_risk_flag = meds.filter(risk_flag=True).exists()

        # Hormone test results
        hormone_tests = HormoneTest.objects.filter(batch=batch)
        test_summary = {
            "total": hormone_tests.count(),
            "passed": hormone_tests.filter(result="pass").count(),
            "failed": hormone_tests.filter(result="fail").count(),
        }

        # Withdrawal period check
        from django.utils import timezone
        today = timezone.now().date()
        withdrawal_clear = not meds.filter(
            administered_at__date__gt=today - timezone.timedelta(
                days=max(meds.values_list("withdrawal_period_days", flat=True) or [0])
            )
        ).exists()

        return Response({
            "batch_code": batch.batch_code,
            "species": batch.get_species_display(),
            "arrival_date": batch.arrival_date,
            "facility": {
                "name": facility.name,
                "state": facility.get_state_display(),
                "fssai_license": facility.fssai_license,
                "compliance_status": facility.get_compliance_status_display(),
                "risk_score": round(facility.risk_score, 2),
            },
            "medications": {
                "antibiotic_administrations": antibiotic_count,
                "hormone_administrations": hormone_count,
                "risk_flagged": any_risk_flag,
                "withdrawal_period_clear": withdrawal_clear,
            },
            "hormone_tests": test_summary,
            "overall_safe": (
                not any_risk_flag
                and test_summary["failed"] == 0
                and facility.compliance_status == "compliant"
            ),
        })


class FacilityPublicProfileView(APIView):
    """Public compliance profile for a facility, accessible by FSSAI license number."""
    permission_classes = [AllowAny]

    def get(self, request, fssai_license):
        try:
            facility = Facility.objects.get(fssai_license=fssai_license, is_active=True)
        except Facility.DoesNotExist:
            return Response({"error": "Facility not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "name": facility.name,
            "facility_type": facility.get_facility_type_display(),
            "state": facility.get_state_display(),
            "fssai_license": facility.fssai_license,
            "compliance_status": facility.get_compliance_status_display(),
            "risk_score": round(facility.risk_score, 2),
            "animal_capacity": facility.animal_capacity,
        })
