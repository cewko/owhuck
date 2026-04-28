from django.db.models import Avg, Count
from apps.deliveries.models import DeliveryAttempt
from apps.replays.models import EventReplay
from apps.webhooks.models import WebhookEvent


class MetricsService:
    def get_metrics(self) -> dict:
        event_count = self._event_count()
        delivery_count = self._delivery_count()
        total_events = sum(event_count.values())
        successful_events = event_count.get(WebhookEvent.Status.SUCCESS, 0)

        return {
            "events": {
                "total": total_events,
                "received": event_count.get(WebhookEvent.Status.RECEIVED, 0),
                "queued": event_count.get(WebhookEvent.Status.QUEUED, 0),
                "delivering": event_count.get(WebhookEvent.Status.DELIVERING, 0),
                "success": successful_events,
                "retrying": event_count.get(WebhookEvent.Status.RETRYING, 0),
                "failed": event_count.get(WebhookEvent.Status.FAILED, 0),
                "cancelled": event_count.get(WebhookEvent.Status.CANCELLED, 0),
                "success_rate": self._rate(successful_events, total_events),
            },
            "deliveries": {
                "total_attempts": sum(delivery_count.values()),
                "running": delivery_count.get(DeliveryAttempt.Status.RUNNING, 0),
                "success": delivery_count.get(DeliveryAttempt.Status.SUCCESS, 0),
                "failed": delivery_count.get(DeliveryAttempt.Status.FAILED, 0),
                "average_duration_ms": self._average_duration_ms(),
            },
            "replays": {
                "total": EventReplay.objects.count(),
            },
        }

    def _event_count(self) -> dict:
        rows = (
            WebhookEvent.objects
            .values("status")
            .annotate(total=Count("pkid"))
        )

        return {row["status"]: row["total"] for row in rows}

    def _delivery_count(self) -> dict:
        rows = (
            DeliveryAttempt.objects
            .values("status")
            .annotate(total=Count("pkid"))
        )

        return {row["status"]: row["total"] for row in rows}

    def _average_duration_ms(self) -> int | None:
        delivery = DeliveryAttempt.objects.aggregate(
            average=Avg("duration_ms")
        )

        if delivery["average"] is None:
            return None

        return round(delivery["average"])

    def _rate(self, value: int, total: int) -> float:
        if total == 0:
            return 0.0

        return round(value / total, 4)