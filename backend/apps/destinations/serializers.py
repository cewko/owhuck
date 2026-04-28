from rest_framework import serializers

from .models import Destination


class DestinationSerializer(serializers.ModelSerializer):
    incoming_signature_key = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = Destination
        fields = [
            "id",
            "name",
            "target_url",
            "status",
            "incoming_signature_key",
            "signature_verification_mode",
            "max_retries",
            "timeout_seconds",
            "retry_backoff_base_seconds",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DestinationCreateSerializer(serializers.ModelSerializer):
    signing_key = serializers.CharField(read_only=True)

    class Meta:
        model = Destination
        fields = [
            "id",
            "name",
            "target_url",
            "status",
            "signing_key",
            "signature_verification_mode",
            "incoming_signature_key",
            "max_retries",
            "timeout_seconds",
            "retry_backoff_base_seconds",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "signing_key", "created_at", "updated_at"]