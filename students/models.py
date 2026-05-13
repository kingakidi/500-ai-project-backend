from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from core.models import BaseModel
from departments.models import Department


student_reg_no_validator = RegexValidator(
    regex=r"^u\d{2}[a-zA-Z]{2,4}\d{4}$",
    message=(
        "Invalid registration number format. Example: u21co1001, u21mls1001, u21msde1001."
    ),
)


class Student(BaseModel):
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="students"
    )
    full_name = models.CharField(max_length=255)
    registration_number = models.CharField(
        max_length=20, unique=True, validators=[student_reg_no_validator]
    )
    profile_image = models.URLField(blank=True, null=True)
    fingerprint_template_slot = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(127)],
        help_text="On-sensor template slot (1–127). Device returns this slot on scan for lookup.",
    )

    class Meta(BaseModel.Meta):
        db_table = "students"

    def __str__(self) -> str:
        return f"{self.registration_number} - {self.full_name}"

