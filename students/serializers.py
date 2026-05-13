from rest_framework import serializers

from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "id",
            "created_at",
            "updated_at",
            "department",
            "full_name",
            "registration_number",
            "profile_image",
            "fingerprint_template_slot",
        ]
        read_only_fields = ("fingerprint_template_slot",)

    def validate_registration_number(self, value: str) -> str:
        return value.strip().lower()

