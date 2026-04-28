from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "action",
        "entity_type",
        "entity_id",
        "actor",
        "ip_address",
        "created_at",
    ]

    list_filter = [
        "action",
        "entity_type",
        "created_at",
    ]

    search_fields = [
        "id",
        "entity_type",
        "entity_id",
        "actor__username",
        "actor__email",
        "ip_address",
    ]

    readonly_fields = [
        "pkid",
        "id",
        "actor",
        "action",
        "entity_type",
        "entity_id",
        "ip_address",
        "user_agent",
        "metadata",
        "created_at",
        "updated_at",
    ]

    ordering = ["-created_at"]

    fieldsets = [
        (
            "Audit Event",
            {
                "fields": [
                    "pkid",
                    "id",
                    "action",
                    "actor",
                ]
            },
        ),
        (
            "Entity",
            {
                "fields": [
                    "entity_type",
                    "entity_id",
                ]
            },
        ),
        (
            "Request Context",
            {
                "fields": [
                    "ip_address",
                    "user_agent",
                ]
            },
        ),
        (
            "Metadata",
            {
                "fields": [
                    "metadata",
                ]
            },
        ),
        (
            "Timestamps",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    def has_add_permission(self, request):
        return False
