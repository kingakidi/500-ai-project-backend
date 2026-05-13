from rest_framework import serializers

from .models import Faculty


class FacultySerializer(serializers.ModelSerializer):
    dean_name = serializers.CharField(source="leader_name")
    dean_phone = serializers.CharField(source="leader_phone")
    dean_email = serializers.EmailField(source="leader_email")

    class Meta:
        model = Faculty
        fields = [
            "id",
            "created_at",
            "updated_at",
            "name",
            "dean_name",
            "dean_phone",
            "dean_email",
        ]

