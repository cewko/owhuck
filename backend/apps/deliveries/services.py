import hashlib
import hmac
import json
import time
from dataclasses import dataclass

import httpx
from django.db import transaction
from django.utils import timezone

from apps.webhooks.models import WebhookEvent
from apps.audit.models import AuditLog
from apps.audit.services import create_audit_log
from .models import DeliveryAttempt
from .retry import RetryPolicy


MAX_RESPONSE_BODY_LENGTH = 10_000


@dataclass(frozen=True)
class DeliveryResult:
    status_code: int | None
    headers: dict
    body: str
    error_message: str
    duration_ms: int

    @property
    def is_success(self) -> bool:
        return self.status_code is not None and 200 <= self.status_code < 300


class WebhookDeliveryClient:
    def send(self, attempt: DeliveryAttempt) -> DeliveryResult:
        started_at = time.monotonic()

        try:
            response = httpx.post(
                attempt.request_url,
                content=self._serialize_body(attempt.request_body),
                headers=attempt.request_headers,
                timeout=attempt.destination.timeout_seconds,
            )

            return DeliveryResult(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.text[:MAX_RESPONSE_BODY_LENGTH],
                error_message="",
                duration_ms=self._duration_ms(started_at)
            )

        except httpx.TimeoutException:
            return self._failed_result(started_at, "Timeout while delivering")

        except httpx.RequestError as _e:
            return self._failed_result(started_at, str(_e))

    def _serialize_body(self, body: dict) -> bytes:
        return json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode()

    def _duration_ms(self, started_at: float) -> int:
        return int((time.monotonic() - started_at) * 1000)

    def _failed_result(self, started_at: float, message: str) -> DeliveryResult:
        return DeliveryResult(
            status_code=None,
            headers={},
            body="",
            error_message=message,
            duration_ms=self._duration_ms(started_at)
        )


class DeliveryService:
    def __init__(
        self, 
        client: WebhookDeliveryClient | None = None,
        retry_policy: RetryPolicy | None = None
    ):
        self.client = client or WebhookDeliveryClient()
        self.retry_policy = retry_policy or RetryPolicy()

    def deliver(self, event_id: str) -> None:
        attempt = self._start_attempt(event_id)
        result = self.client.send(attempt)

        self._finish_attempt(attempt, result)
        self._update_event_status(attempt.event, result, attempt)

    @transaction.atomic
    def _start_attempt(self, event_id: str) -> DeliveryAttempt:
        event = (
            WebhookEvent.objects
            .select_for_update()
            .select_related("destination")
            .get(id=event_id)
        )

        attempt_number = event.delivery_attempts.count() + 1

        event.status = WebhookEvent.Status.DELIVERING
        event.save(update_fields=["status", "updated_at"])

        return DeliveryAttempt.objects.create(
            event=event,
            destination=event.destination,
            attempt_number=attempt_number,
            status=DeliveryAttempt.Status.RUNNING,
            request_url=event.destination.target_url,
            request_headers=self._build_headers(event, attempt_number),
            request_body=event.payload,
            scheduled_at=timezone.now(),
            started_at=timezone.now(),
        )

    def _finish_attempt(self, attempt: DeliveryAttempt, result: DeliveryResult) -> None:
        attempt.status = (
            DeliveryAttempt.Status.SUCCESS
            if result.is_success
            else DeliveryAttempt.Status.FAILED
        )
        attempt.response_status_code = result.status_code
        attempt.response_headers = result.headers
        attempt.response_body = result.body
        attempt.error_message = result.error_message
        attempt.duration_ms = result.duration_ms
        attempt.finished_at = timezone.now()
        attempt.save()

    def _schedule_retry(self, event: WebhookEvent, delay_seconds: int) -> None:
        from .tasks import deliver_webhook

        deliver_webhook.apply_async(
            args=[str(event.id)],
            countdown=delay_seconds
        )

    def _update_event_status(
        self, 
        event: WebhookEvent, 
        result: DeliveryResult,
        attempt: DeliveryAttempt
    ) -> None:
        if result.is_success:
            event.status = WebhookEvent.Status.SUCCESS
            event.delivered_at = timezone.now()
            event.failed_at = None
            event.next_retry_at = None
            event.save(update_fields=[
                "status", 
                "delivered_at", 
                "updated_at",
                "failed_at",
                "next_retry_at",
                "updated_at"
            ])

            create_audit_log(
                action=AuditLog.Action.DELIVERY_SUCCEEDED,
                entity=event,
                metadata={
                    "attempt_id": str(attempt.id),
                    "attempt_number": attempt.attempt_number,
                    "destination_id": str(event.destination.id),
                    "status_code": result.status_code,
                    "duration_ms": result.duration_ms
                }
            )

            return

        if self.retry_policy.should_retry(
            attempt_count=attempt.attempt_number,
            max_retries=event.destination.max_retries
        ):
            delay_seconds = self.retry_policy.calculate_delay_seconds(
                base_seconds=event.destination.retry_backoff_base_seconds,
                attempt_number=attempt.attempt_number
            )

            event.status = WebhookEvent.Status.RETRYING
            event.failed_at = None
            event.next_retry_at = self.retry_policy.calculate_next_retry_at(delay_seconds)
            event.save(update_fields=[
                "status", 
                "failed_at",
                "next_retry_at", 
                "updated_at"
            ])

            self._schedule_retry(event, delay_seconds)
            return

        event.status = WebhookEvent.Status.FAILED
        event.failed_at = timezone.now()
        event.next_retry_at = None
        event.save(update_fields=[
            "status",
            "failed_at",
            "next_retry_at",
            "updated_at"
        ])

        create_audit_log(
            action=AuditLog.Action.DELIVERY_FAILED,
            entity=event,
            metadata={
                "attempt_id": str(attempt.id),
                "attempt_number": attempt.attempt_number,
                "destination_id": str(event.destination.id),
                "status_code": result.status_code,
                "error_message": result.error_message
            }
        )

    def _build_headers(self, event: WebhookEvent, attempt_number: int) -> dict:
        body = json.dumps(event.payload, separators=(",", ":"), ensure_ascii=False).encode()
        timestamp = str(int(timezone.now().timestamp()))

        signature = hmac.new(
            key=event.destination.signing_key.encode(),
            msg=timestamp.encode() + b"." + body,
            digestmod=hashlib.sha256
        ).hexdigest()

        return {
            "Content-Type": "application/json",
            "X-Relay-Event-Id": str(event.id),
            "X-Relay-Attempt": str(attempt_number),
            "X-Relay-Timestamp": timestamp,
            "X-Relay-Signature": f"sha256={signature}",
        }

    