import sys

from django.apps import AppConfig


class FingerprintReaderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fingerprint_reader"
    verbose_name = "Fingerprint reader"

    def ready(self):
        argv_joined = " ".join(sys.argv).lower()
        if any(
            token in argv_joined
            for token in (
                "migrate",
                "makemigrations",
                "sqlmigrate",
                "test",
                "pytest",
                "collectstatic",
                "check",
                "shell",
            )
        ):
            return
        try:
            from django.conf import settings

            if not getattr(settings, "FINGERPRINT_READER_START_THREAD", True):
                return
            from fingerprint_reader.services import hardware

            hardware.ensure_reader_running()
        except ImportError:
            pass
