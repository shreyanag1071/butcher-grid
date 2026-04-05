import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Avg, Q

logger = logging.getLogger(__name__)


@shared_task
def generate_weekly_compliance_reports():
    """
    Every Monday: recalculate risk scores for all active facilities
    and flip compliance status based on thresholds.
    """
    from core.models import Facility, Alert
    from apps.farm_monitor.models import MedicationLog, HormoneTest
    from apps.waste_tracker.models import WasteDisposalLog

    cutoff = timezone.now() - timezone.timedelta(days=7)
    updated = 0

    for facility in Facility.objects.filter(is_active=True):
        # Component scores (0.0 - 1.0 each)
        flagged_meds = MedicationLog.objects.filter(
            batch__facility=facility, risk_flag=True, created_at__gte=cutoff
        ).count()

        hormone_failures = HormoneTest.objects.filter(
            batch__facility=facility, result="fail"
        ).count()

        waste_anomalies = WasteDisposalLog.objects.filter(
            facility=facility, is_anomaly=True, logged_at__gte=cutoff
        ).count()

        open_alerts = Alert.objects.filter(
            facility=facility, is_resolved=False,
            severity__in=["high", "critical"]
        ).count()

        # Weighted composite risk score
        med_score = min(flagged_meds / 5.0, 1.0) * 0.35
        hormone_score = min(hormone_failures / 3.0, 1.0) * 0.30
        waste_score = min(waste_anomalies / 3.0, 1.0) * 0.25
        alert_score = min(open_alerts / 2.0, 1.0) * 0.10
        composite = med_score + hormone_score + waste_score + alert_score

        # Derive compliance status
        if composite >= 0.75:
            compliance = Facility.ComplianceStatus.NON_COMPLIANT
        elif composite >= 0.45:
            compliance = Facility.ComplianceStatus.WARNING
        else:
            compliance = Facility.ComplianceStatus.COMPLIANT

        Facility.objects.filter(id=facility.id).update(
            risk_score=round(composite, 4),
            compliance_status=compliance,
        )

        if compliance == Facility.ComplianceStatus.NON_COMPLIANT:
            Alert.objects.create(
                facility=facility,
                alert_type=Alert.AlertType.COMPLIANCE_BREACH,
                severity="critical",
                message=(
                    f"Weekly compliance check: {facility.name} scored {composite:.2f}. "
                    f"Flagged medications: {flagged_meds}, hormone failures: {hormone_failures}, "
                    f"waste anomalies: {waste_anomalies}."
                ),
            )

        updated += 1

    logger.info("Weekly compliance reports generated for %d facilities.", updated)


@shared_task
def send_farmer_alerts():
    """
    Notify farm owners of unresolved high/critical alerts via SMS/WhatsApp.
    Stub — wire to Twilio or WhatsApp Business API.
    """
    from core.models import Alert

    pending = Alert.objects.filter(
        is_resolved=False,
        severity__in=["high", "critical"],
        created_at__gte=timezone.now() - timezone.timedelta(hours=24),
    ).select_related("facility__owner")

    for alert in pending:
        owner = alert.facility.owner
        if owner.phone:
            _send_sms(owner.phone, f"[Butcher Grid] {alert.message}")
            logger.info("Alert SMS sent to %s for facility %s", owner.phone, alert.facility.name)


def _send_sms(phone: str, message: str):
    """Stub — replace with Twilio client call."""
    logger.debug("SMS → %s: %s", phone, message)
