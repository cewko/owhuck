from django.contrib.auth.models import AnonymousUser
from .models import AuditLog


def create_audit_log(
    *,
    action: str,
    actor=None,
    entity=None,
    request=None,
    metadata: dict | None = None
) -> AuditLog:
    return AuditLog.objects.create(
        actor=_get_actor(actor),
        action=action,
        entity_type=_get_entity_type(entity),
        entity_id=_get_entity_id(entity),
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        metadata=metadata or {}
    )


def _get_actor(actor):
    if actor is None or isinstance(actor, AnonymousUser):
        return None

    if not getattr(actor, "is_authenticated", False):
        return None

    return actor


def _get_entity_type(entity) -> str:
    if entity is None:
        return ""

    return entity._meta.label


def _get_entity_id(entity):
    if entity is None:
        return None

    return getattr(entity, "id", None)


def _get_client_ip(request):
    if request is None:
        return None

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def _get_user_agent(request) -> str:
    if request is None:
        return ""

    return request.META.get("HTTP_USER_AGENT", "")