import logging
import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def score_waste_anomaly(self, waste_log_id: str):
    from .models import WasteDisposalLog
    from core.models import Alert

    try:
        log = WasteDisposalLog.objects.select_related("facility").get(id=waste_log_id)
    except WasteDisposalLog.DoesNotExist:
        return

    payload = {
        "facility_id": str(log.facility.id),
        "waste_type": log.waste_type,
        "quantity_kg": log.quantity_kg,
        "disposal_method": log.disposal_method,
        "logged_at": log.logged_at.isoformat(),
    }

    try:
        resp = requests.post(
            f"{settings.ML_SERVICE_URL}/predict/waste-anomaly",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        score = result.get("anomaly_score", 0.0)
        is_anomaly = score >= settings.WASTE_ANOMALY_THRESHOLD

        WasteDisposalLog.objects.filter(id=waste_log_id).update(
            anomaly_score=score, is_anomaly=is_anomaly
        )

        if is_anomaly:
            Alert.objects.create(
                facility=log.facility,
                alert_type=Alert.AlertType.WASTE_ANOMALY,
                severity="high" if score >= 0.9 else "medium",
                message=(
                    f"Anomalous waste disposal detected: {log.quantity_kg}kg of "
                    f"{log.waste_type} via {log.disposal_method}. Score: {score:.2f}."
                ),
            )
    except requests.RequestException as exc:
        logger.error("ML service error on waste anomaly: %s", exc)
        raise self.retry(exc=exc)


@shared_task
def detect_waste_anomalies_all_facilities():
    """Nightly re-scan of yesterday's waste logs."""
    from django.utils import timezone
    from .models import WasteDisposalLog

    yesterday = timezone.now() - timezone.timedelta(days=1)
    logs = WasteDisposalLog.objects.filter(logged_at__date=yesterday.date()).values_list("id", flat=True)
    for log_id in logs:
        score_waste_anomaly.delay(str(log_id))
    logger.info("Queued waste anomaly scoring for %d logs", logs.count())
