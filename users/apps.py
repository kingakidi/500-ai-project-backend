from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        """Automatically create super admin user from environment variables on system initialization"""
        import os
        import sys
        import environ
        
        if os.environ.get("RUN_MAIN") != "true":
            return
        
        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            return
        
        try:
            from django.db import connection
            
            if not connection.introspection.table_names():
                return
            
            env = environ.Env()
            
            admin_email = env("SUPERADMIN_EMAIL", default=None)
            admin_password = env("SUPERADMIN_PASSWORD", default=None)
            
            if not admin_email or not admin_password:
                return
            
            from users.models import User
            
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
                return
            
            email_parts = admin_email.split("@")[0]
            first_name = env("SUPERADMIN_FIRST_NAME", default=email_parts.capitalize())
            last_name = env("SUPERADMIN_LAST_NAME", default="Admin")
            
            User.objects.create_superuser(
                email=admin_email,
                password=admin_password,
                first_name=first_name,
                last_name=last_name,
                role="superadmin",
            )
        except Exception:
            pass
