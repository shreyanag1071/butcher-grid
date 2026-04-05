from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WasteDisposalLogViewSet, EnvironmentalReadingViewSet

router = DefaultRouter()
router.register("logs", WasteDisposalLogViewSet, basename="waste-log")
router.register("env-readings", EnvironmentalReadingViewSet, basename="env-reading")

urlpatterns = [path("", include(router.urls))]
