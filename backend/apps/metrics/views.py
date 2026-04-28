from rest_framework.response import Response
from rest_framework.views import APIView

from .services import MetricsService


class MetricsView(APIView):
    def get(self, request):
        metrics = MetricsService().get_metrics()
        return Response(metrics)