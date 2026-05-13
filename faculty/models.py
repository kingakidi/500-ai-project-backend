from django.db import models

from core.models import LeadershipContact


class Faculty(LeadershipContact):
    name = models.CharField(max_length=255, unique=True)

    class Meta(LeadershipContact.Meta):
        db_table = "faculties"

    def __str__(self) -> str:
        return self.name

