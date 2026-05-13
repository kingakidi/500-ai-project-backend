from rest_framework import serializers

from .models import Course


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "created_at",
            "updated_at",
            "department",
            "course_title",
            "course_code",
            "credit_unit",
            "semester",
        ]

