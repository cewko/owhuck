from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from apps.common.models import TimeStampedModel, UUIDModel
from .services import generate_signing_key


class Destination(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DISABLED = "disabled", "Disabled"

    name = models.CharField(max_length=120)
    target_url = models.URLField(max_length=2048)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True
    )

    signing_key = models.CharField(
        max_length=255,
        default=generate_signing_key,
        editable=False
    )

    max_retries = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    timeout_seconds = models.PositiveSmallIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
    )
    retry_backoff_base_seconds = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(300)],
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"])
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_retries__gte=0) 
                & models.Q(max_retries__lte=20),
                name="destination_max_retries_range",
            ),
            models.CheckConstraint(
                condition=models.Q(timeout_seconds__gte=1) 
                & models.Q(timeout_seconds__lte=60),
                name="destination_timeout_seconds_range",
            ),
            models.CheckConstraint(
                condition=models.Q(retry_backoff_base_seconds__gte=1)
                & models.Q(retry_backoff_base_seconds__lte=300),
                name="destination_retry_backoff_base_seconds_range",
            ),
        ]

    def __str__(self):
        return self.name