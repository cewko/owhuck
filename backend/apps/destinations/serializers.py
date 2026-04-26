from rest_framework import serializers

from .models import Destination


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = [
            "id",
            "name",
            "target_url",
            "status",
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
            "max_retries",
            "timeout_seconds",
            "retry_backoff_base_seconds",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "signing_key", "created_at", "updated_at"]