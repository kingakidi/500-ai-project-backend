from django.urls import path

from .views import PresignDownloadView, PresignUploadView

app_name = "s3_upload"

urlpatterns = [
    path("presign-upload", PresignUploadView.as_view(), name="presign-upload"),
    path("presign-download", PresignDownloadView.as_view(), name="presign-download"),
]

