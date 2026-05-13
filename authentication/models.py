import random
import string
from datetime import timedelta

from core.models import BaseModel
from django.db import models
from django.utils import timezone


class OTP(BaseModel):

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="otps"
    )
    code = models.CharField(max_length=4)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    purpose = models.CharField(max_length=50, default="login")

    class Meta:
        db_table = "otps"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "code", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"OTP for {self.user.email} - {self.code}"

    @classmethod
    def generate_code(cls, length=4):
        return "".join(random.choices(string.digits, k=length))

    @classmethod
    def create_otp(cls, user, purpose="login", expiry_hours=24):
        cls.objects.filter(
            user=user, purpose=purpose, is_used=False, expires_at__gt=timezone.now()
        ).update(is_used=True)

        code = cls.generate_code()
        expires_at = timezone.now() + timedelta(hours=expiry_hours)

        otp = cls.objects.create(
            user=user, code=code, expires_at=expires_at, purpose=purpose
        )
        return otp

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    def mark_as_used(self):
        self.is_used = True
        self.save(update_fields=["is_used"])


class OTPThrottle(BaseModel):
    email = models.EmailField()
    purpose = models.CharField(max_length=50, default="login")
    kind = models.CharField(max_length=20)  # "send" or "try"
    bucket = models.DateTimeField()

    class Meta:
        db_table = "otp_throttle"
        indexes = [
            models.Index(fields=["email", "purpose", "kind", "bucket"]),
            models.Index(fields=["bucket"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["email", "purpose", "kind", "bucket"],
                name="uniq_otp_throttle_email_purpose_kind_bucket",
            )
        ]
