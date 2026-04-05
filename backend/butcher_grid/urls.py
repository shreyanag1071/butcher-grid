from django.urls import path
from .views import (
    RegisterView, ProfileView,
    FacilityListCreateView, FacilityDetailView,
    BatchListCreateView,
    MedicationListCreateView,
    WasteListCreateView,
    AlertListView, AlertResolveView,
    QRScanView,
    DashboardView,
)

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view()),
    path("auth/profile/", ProfileView.as_view()),

    # Facilities
    path("facilities/", FacilityListCreateView.as_view()),
    path("facilities/<uuid:pk>/", FacilityDetailView.as_view()),

    # Batches
    path("batches/", BatchListCreateView.as_view()),

    # Medications — AI scored on POST
    path("medications/", MedicationListCreateView.as_view()),

    # Waste — AI scored on POST
    path("waste/", WasteListCreateView.as_view()),

    # Alerts
    path("alerts/", AlertListView.as_view()),
    path("alerts/<uuid:pk>/resolve/", AlertResolveView.as_view()),

    # Public QR scan — no auth
    path("scan/<str:qr_code>/", QRScanView.as_view()),

    # Regulator dashboard
    path("dashboard/", DashboardView.as_view()),
]
