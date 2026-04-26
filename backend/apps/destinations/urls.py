from rest_framework.routers import DefaultRouter
from .views import DestinationViewSet


router = DefaultRouter()
router.register("destinations", DestinationViewSet, basename="destination")

urlpatterns = router.urls