from django.core.validators import MinValueValidator
from django.db import models

from core.models import BaseModel
from departments.models import Department


class Course(BaseModel):
    SEMESTER_CHOICES = [(1, "1"), (2, "2")]

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="courses"
    )
    course_title = models.CharField(max_length=255)
    course_code = models.CharField(max_length=50)
    credit_unit = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    semester = models.PositiveSmallIntegerField(choices=SEMESTER_CHOICES)

    class Meta(BaseModel.Meta):
        db_table = "courses"
        constraints = [
            models.UniqueConstraint(
                fields=["department", "course_code"], name="unique_course_code_per_dept"
            )
        ]

    def __str__(self) -> str:
        return f"{self.course_code} - {self.course_title}"

