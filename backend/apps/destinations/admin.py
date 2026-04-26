from django.contrib import admin

from .models import Destination


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "target_url",
        "status",
        "max_retries",
        "timeout_seconds",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["id", "name", "target_url"]
    readonly_fields = ["pkid", "id", "signing_key", "created_at", "updated_at"]

