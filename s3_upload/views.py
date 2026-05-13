from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.response import APIResponse

from .client import get_s3_client
from .serializers import PresignDownloadSerializer, PresignUploadSerializer


class PresignUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PresignUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        key = serializer.validated_data["key"].lstrip("/")
        expires_in = serializer.validated_data.get("expires_in", 900)
        content_type = serializer.validated_data.get("content_type") or None

        bucket = getattr(settings, "S3_BUCKET_NAME", None)
        if not bucket:
            return APIResponse.server_error(
                "S3 bucket is not configured",
                error={"S3_BUCKET_NAME": ["Missing S3_BUCKET_NAME in environment."]},
            )

        s3 = get_s3_client()
        params = {"Bucket": bucket, "Key": key}
        if content_type:
            params["ContentType"] = content_type

        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=expires_in,
        )

        return APIResponse.success(
            "Presigned upload URL generated",
            {
                "bucket": bucket,
                "key": key,
                "upload_url": url,
                "expires_in": expires_in,
            },
        )


class PresignDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PresignDownloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        key = serializer.validated_data["key"].lstrip("/")
        expires_in = serializer.validated_data.get("expires_in", 900)

        bucket = getattr(settings, "S3_BUCKET_NAME", None)
        if not bucket:
            return APIResponse.server_error(
                "S3 bucket is not configured",
                error={"S3_BUCKET_NAME": ["Missing S3_BUCKET_NAME in environment."]},
            )

        s3 = get_s3_client()
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

        return APIResponse.success(
            "Presigned download URL generated",
            {
                "bucket": bucket,
                "key": key,
                "download_url": url,
                "expires_in": expires_in,
            },
        )

