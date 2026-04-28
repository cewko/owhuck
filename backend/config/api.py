from django.urls import include, path

urlpatterns = [
    path('', include("apps.common.urls")),
    path('', include("apps.destinations.urls")),
    path("", include("apps.webhooks.urls")),
    path("", include("apps.deliveries.urls")),
    path("", include("apps.audit.urls")),
    path("", include("apps.replays.urls")),
    path("", include("apps.metrics.urls")),
]
