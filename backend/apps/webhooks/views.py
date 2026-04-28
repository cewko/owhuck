from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.audit.models import AuditLog
from apps.audit.services import create_audit_log

from apps.destinations.models import Destination
from .serializers import (
    IngestWebhookResponseSerializer, 
    WebhookEventSerializer
)
from .exceptions import DestinationInactiveError
from .models import WebhookEvent
from .services import (
    IngestWebhookRequest,
    IngestWebhookService,
)


class WebhookIngestView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, destination_id):
        service = IngestWebhookService()

        raw_body = request.body
        payload = request.data

        try:
            result = service.ingest(
                IngestWebhookRequest(
                    destination_id=destination_id,
                    method=request.method,
                    headers=dict(request.headers),
                    query_params=request.query_params.dict(),
                    payload=payload,
                    raw_body=raw_body,
                )
            )

            create_audit_log(
                action=AuditLog.Action.WEBHOOK_RECEIVED,
                entity=result.event,
                request=request,
                metadata={
                    "destination_id": str(result.event.destination.id),
                    "method": request.method,
                    "idempotency_key": result.event.idempotency_key,
                    "created": result.created
                }
            )
        except Destination.DoesNotExist:
            return Response(
                {"detail": "Destination not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except DestinationInactiveError:
            return Response(
                {"detail": "Destination is disabled."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = IngestWebhookResponseSerializer(result)
        response_status = (
            status.HTTP_202_ACCEPTED
            if result.created
            else status.HTTP_200_OK
        )

        return Response(serializer.data, status=response_status)


class WebhookEventViewSet(ReadOnlyModelViewSet):
    serializer_class = WebhookEventSerializer
    lookup_field = "id"

    def get_queryset(self):
        queryset = WebhookEvent.objects.select_related("destination")

        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        destination_id = self.request.query_params.get("destination")
        if destination_id:
            queryset = queryset.filter(destination__id=destination_id)

        return queryset