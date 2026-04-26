from rest_framework.viewsets import ModelViewSet

from .models import Destination
from .serializers import DestinationSerializer, DestinationCreateSerializer


class DestinationViewSet(ModelViewSet):
    queryset = Destination.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action == "create":
            return DestinationCreateSerializer
        return DestinationSerializer
