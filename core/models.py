import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class LeadershipContact(BaseModel):
    """
    Shared leader contact fields for Faculty/Department-like entities.
    """

    leader_name = models.CharField(max_length=255)
    leader_phone = models.CharField(max_length=50)
    leader_email = models.EmailField()

    class Meta(BaseModel.Meta):
        abstract = True

