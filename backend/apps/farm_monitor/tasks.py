import logging
import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_medication_risk_score(self, medication_log_id: str):
    """
    Call the ML service to score antibiotic/hormone risk for a single log entry.
    Updates the log with the returned score and flags alerts if threshold exceeded.
    """
    from .models import MedicationLog
    from core.models import Alert

    try:
        log = MedicationLog.objects.select_related("batch__facility").get(id=medication_log_id)
    except MedicationLog.DoesNotExist:
        logger.error("MedicationLog %s not found", medication_log_id)
        return

    payload = {
        "medication_name": log.medication_name,
        "medication_type": log.medication_type,
        "dosage_mg": log.dosage_mg,
        "withdrawal_period_days": log.withdrawal_period_days,
        "batch_id": str(log.batch.id),
        "species": log.batch.species,
    }

    try:
        resp = requests.post(
            f"{settings.ML_SERVICE_URL}/predict/medication-risk",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        risk_score = result.get("risk_score", 0.0)
        risk_flag = risk_score >= settings.HORMONE_FLAG_THRESHOLD

        MedicationLog.objects.filter(id=medication_log_id).update(
            risk_score=risk_score, risk_flag=risk_flag
        )

        if risk_flag:
            severity = "critical" if risk_score >= 0.9 else "high" if risk_score >= 0.75 else "medium"
            Alert.objects.create(
                facility=log.batch.facility,
                alert_type=Alert.AlertType.ANTIBIOTIC_OVERUSE
                if log.medication_type == "antibiotic"
                else Alert.AlertType.HORMONE_FLAG,
                severity=severity,
                message=(
                    f"Risk score {risk_score:.2f} flagged for {log.medication_name} "
                    f"in batch {log.batch.batch_code}."
                ),
            )
            logger.warning("Alert raised for MedicationLog %s, score=%.2f", medication_log_id, risk_score)

    except requests.RequestException as exc:
        logger.error("ML service unreachable: %s — retrying", exc)
        raise self.retry(exc=exc)


@shared_task
def score_all_farms_antibiotic_risk():
    """
    Periodic task: re-score recent medication logs across all active facilities.
    Runs every 6 hours via Celery Beat.
    """
    from .models import MedicationLog

    cutoff = timezone.now() - timezone.timedelta(hours=12)
    logs = MedicationLog.objects.filter(created_at__gte=cutoff).values_list("id", flat=True)
    for log_id in logs:
        run_medication_risk_score.delay(str(log_id))
    logger.info("Queued risk scoring for %d recent medication logs", logs.count())
