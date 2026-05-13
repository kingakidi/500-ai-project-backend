from rest_framework import serializers


class PresignUploadSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=512)
    content_type = serializers.CharField(max_length=255, required=False, allow_blank=True)
    expires_in = serializers.IntegerField(required=False, min_value=60, max_value=3600)


class PresignDownloadSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=512)
    expires_in = serializers.IntegerField(required=False, min_value=60, max_value=3600)

