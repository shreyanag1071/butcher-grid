from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FacilityRegulatoryViewSet, AlertViewSet, NationalDashboardView

router = DefaultRouter()
router.register("facilities", FacilityRegulatoryViewSet, basename="reg-facility")
router.register("alerts", AlertViewSet, basename="reg-alert")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", NationalDashboardView.as_view(), name="national-dashboard"),
]
