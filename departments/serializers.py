from rest_framework import serializers

from .models import Department


class DepartmentSerializer(serializers.ModelSerializer):
    head_of_department_name = serializers.CharField(source="leader_name")
    head_of_department_phone = serializers.CharField(source="leader_phone")
    head_of_department_email = serializers.EmailField(source="leader_email")

    class Meta:
        model = Department
        fields = [
            "id",
            "created_at",
            "updated_at",
            "faculty",
            "name",
            "head_of_department_name",
            "head_of_department_phone",
            "head_of_department_email",
        ]

