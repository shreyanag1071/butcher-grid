import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("butcher_grid")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Run antibiotic risk scoring for all farms every 6 hours
    "score-antibiotic-risk": {
        "task": "apps.farm_monitor.tasks.score_all_farms_antibiotic_risk",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Daily waste anomaly detection at midnight IST
    "detect-waste-anomalies": {
        "task": "apps.waste_tracker.tasks.detect_waste_anomalies_all_facilities",
        "schedule": crontab(minute=0, hour=0),
    },
    # Weekly compliance report generation (Monday 7am)
    "generate-compliance-reports": {
        "task": "apps.regulator_api.tasks.generate_weekly_compliance_reports",
        "schedule": crontab(minute=0, hour=7, day_of_week=1),
    },
}
