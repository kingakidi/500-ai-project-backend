from django.conf import settings
from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = "Create super admin user from environment variables"

    def handle(self, *args, **options):
        import environ
        from django.conf import settings

        env = environ.Env()

        # Get super admin credentials from environment
        admin_email = env("SUPERADMIN_EMAIL", default=None)
        admin_password = env("SUPERADMIN_PASSWORD", default=None)

        if not admin_email or not admin_password:
            self.stdout.write(
                self.style.WARNING(
                    "SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD must be set in environment variables."
                )
            )
            return

        if User.objects.filter(email=admin_email).exists():
            user = User.objects.get(email=admin_email)
            updated = False
            if not user.is_superuser:
                user.is_superuser = True
                updated = True
            if not user.is_staff:
                user.is_staff = True
                updated = True
            if user.role != "superadmin":
                user.role = "superadmin"
                updated = True
            
            if updated:
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Super admin '{admin_email}' has been updated with correct role and permissions."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Super admin '{admin_email}' already exists with correct configuration.")
                )
            return

        try:
            email_parts = admin_email.split("@")[0]
            first_name = env("SUPERADMIN_FIRST_NAME", default=email_parts.capitalize())
            last_name = env("SUPERADMIN_LAST_NAME", default="Admin")

            user = User.objects.create_superuser(
                email=admin_email,
                password=admin_password,
                first_name=first_name,
                last_name=last_name,
                role="superadmin",
            )
            self.stdout.write(
                self.style.SUCCESS(f"Super admin '{admin_email}' created successfully.")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating super admin: {str(e)}"))
