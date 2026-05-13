from django.urls import path

from .views import (
    FingerprintEnrollCancelView,
    FingerprintEnrollStartView,
    FingerprintEnrollStatusView,
    FingerprintScanLatestView,
)

app_name = "fingerprint_reader"

urlpatterns = [
    path("enroll/start/", FingerprintEnrollStartView.as_view(), name="fp-enroll-start"),
    path("enroll/status/", FingerprintEnrollStatusView.as_view(), name="fp-enroll-status"),
    path("enroll/cancel/", FingerprintEnrollCancelView.as_view(), name="fp-enroll-cancel"),
    path("scan/latest/", FingerprintScanLatestView.as_view(), name="fp-scan-latest"),
]
