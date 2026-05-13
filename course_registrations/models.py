from django.db import models

from core.models import BaseModel
from courses.models import Course
from students.models import Student


class CourseRegistration(BaseModel):
    SEMESTER_CHOICES = Course.SEMESTER_CHOICES

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="course_registrations"
    )
    semester = models.PositiveSmallIntegerField(choices=SEMESTER_CHOICES)
    session = models.CharField(max_length=32)
    courses = models.ManyToManyField(Course, related_name="registrations", blank=True)

    class Meta(BaseModel.Meta):
        db_table = "course_registrations"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "semester", "session"],
                name="unique_registration_per_student_semester_session",
            )
        ]

    def __str__(self) -> str:
        return f"{self.student.registration_number} - {self.session} (sem {self.semester})"

