from django.db import models

from core.models import LeadershipContact
from faculty.models import Faculty


class Department(LeadershipContact):
    faculty = models.ForeignKey(
        Faculty, on_delete=models.CASCADE, related_name="departments"
    )
    name = models.CharField(max_length=255)

    class Meta(LeadershipContact.Meta):
        db_table = "departments"
        constraints = [
            models.UniqueConstraint(
                fields=["faculty", "name"], name="unique_department_per_faculty"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.faculty.name})"

