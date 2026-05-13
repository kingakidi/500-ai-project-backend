import boto3
from django.conf import settings


def get_s3_client():
    endpoint_url = getattr(settings, "S3_ENDPOINT_URL", None)
    region_name = getattr(settings, "AWS_REGION", None)
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name=region_name,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

