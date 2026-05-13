from rest_framework import serializers

from courses.models import Course

from .models import CourseRegistration


class CourseRegistrationSerializer(serializers.ModelSerializer):
    courses = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Course.objects.all(), required=False
    )

    class Meta:
        model = CourseRegistration
        fields = [
            "id",
            "created_at",
            "updated_at",
            "student",
            "semester",
            "session",
            "courses",
        ]

    def validate(self, attrs):
        semester = attrs.get("semester", getattr(self.instance, "semester", None))
        student = attrs.get("student", getattr(self.instance, "student", None))
        courses = attrs.get("courses", None)

        if courses is not None and semester is not None:
            bad = [c.course_code for c in courses if c.semester != semester]
            if bad:
                raise serializers.ValidationError(
                    {
                        "courses": [
                            f"Courses must match selected semester ({semester}). Offending course(s): {', '.join(bad)}."
                        ]
                    }
                )

        if courses is not None and student is not None:
            bad_dept = [
                c.course_code for c in courses if c.department_id != student.department_id
            ]
            if bad_dept:
                raise serializers.ValidationError(
                    {
                        "courses": [
                            "Student can only register courses in their department. "
                            f"Offending course(s): {', '.join(bad_dept)}."
                        ]
                    }
                )

        return attrs

