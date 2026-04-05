from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicationLogViewSet, HealthRecordViewSet, HormoneTestViewSet

router = DefaultRouter()
router.register("medications", MedicationLogViewSet, basename="medication")
router.register("health-records", HealthRecordViewSet, basename="health-record")
router.register("hormone-tests", HormoneTestViewSet, basename="hormone-test")

urlpatterns = [path("", include(router.urls))]
