from django.urls import path
from .views import BatchTraceView, FacilityPublicProfileView

urlpatterns = [
    path("trace/<str:qr_code>/", BatchTraceView.as_view(), name="batch-trace"),
    path("facility/<str:fssai_license>/", FacilityPublicProfileView.as_view(), name="facility-public"),
]
