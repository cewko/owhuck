from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, UUIDModel


class AuditLog(UUIDModel, TimeStampedModel):
    class Action(models.TextChoices):
        WEBHOOK_RECEIVED = "webhook.received", "Webhook received"
        DELIVERY_SUCCEEDED = "delivery.succeeded", "Delivery succeeded"
        DELIVERY_FAILED = "delivery.failed", "Delivery failed"
        EVENT_REPLAYED = "event.replayed", "Event replayed"
        EVENT_CANCELLED = "event.cancelled", "Event cancelled"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs"
    )
    action = models.CharField(max_length=64, choices=Action.choices, db_index=True)

    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.UUIDField(null=True, blank=True, db_index=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.created_at}"
