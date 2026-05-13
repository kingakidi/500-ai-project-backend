import logging
from urllib.parse import quote

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .models import OTPThrottle

logger = logging.getLogger(__name__)

OTP_TRY_COOLDOWN_SECONDS = 60


def otp_rate_limit_key(kind: str, purpose: str, email: str) -> str:
    normalized_email = (email or "").strip().lower()
    normalized_purpose = (purpose or "login").strip().lower()
    normalized_kind = (kind or "").strip().lower()
    return f"otp:{normalized_kind}:{normalized_purpose}:{normalized_email}"


def allow_otp_action(kind: str, purpose: str, email: str, cooldown_seconds: int = OTP_TRY_COOLDOWN_SECONDS) -> bool:
    normalized_email = (email or "").strip().lower()
    normalized_purpose = (purpose or "login").strip().lower()
    normalized_kind = (kind or "").strip().lower()

    now = timezone.now()
    bucket = now.replace(second=0, microsecond=0)

    try:
        OTPThrottle.objects.create(
            email=normalized_email,
            purpose=normalized_purpose,
            kind=normalized_kind,
            bucket=bucket,
        )
        return True
    except IntegrityError:
        return False


def _send_email(subject: str, template: str, context: dict, recipient: str) -> bool:
    try:
        html_content = render_to_string(template, context)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        logger.info("Email sent successfully to %s (template: %s)", recipient, template)
        return True
    except Exception:
        logger.exception("Failed to send email to %s (template: %s)", recipient, template)
        return False


def send_invitation_email(user, password: str, invited_by=None) -> bool:
    context = {
        "user": user,
        "password": password,
        "site_url": settings.SITE_URL.rstrip("/"),
        "invited_by": invited_by,
    }
    return _send_email(
        subject="You've been invited to Finger Print AI Attendance Verification System",
        template="authentication/invitation_email.html",
        context=context,
        recipient=user.email,
    )


def send_otp_email(user, otp_code: str, purpose: str = "login") -> bool:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    reset_link = ""
    if purpose == "forgot-password":
        encoded_email = quote(user.email, safe="")
        reset_link = f"{frontend_url}/otp?email={encoded_email}&flow=forgot-password"

    context = {
        "user": user,
        "otp_code": otp_code,
        "purpose": purpose,
        "site_url": settings.SITE_URL.rstrip("/"),
        "reset_link": reset_link,
    }
    subject_map = {
        "login": "Your verification code — Finger Print AI Attendance Verification System",
        "forgot-password": "Reset your password — Finger Print AI Attendance Verification System",
    }
    subject = subject_map.get(
        purpose, "Your verification code — Finger Print AI Attendance Verification System"
    )
    return _send_email(
        subject=subject,
        template="authentication/otp_email.html",
        context=context,
        recipient=user.email,
    )
