from rest_framework import viewsets, permissions, mixins, decorators, response, status
from notify.models import Notification
from .serializers import NotificationSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

class NotificationViewSet(mixins.ListModelMixin,
                          mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @decorators.action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        n = self.get_object()
        if not n.is_read:
            n.is_read = True
            n.save(update_fields=["is_read"])
        return response.Response(self.get_serializer(n).data)

    @decorators.action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        qs = self.get_queryset().filter(is_read=False)
        qs.update(is_read=True)
        return response.Response({"updated": qs.count()}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        c = self.get_queryset().filter(is_read=False).count()
        return Response({"count": c})

    @action(detail=False, methods=["get"])
    def recent(self, request):
        qs = self.get_queryset().order_by("-created_at")[:10]
        data = self.get_serializer(qs, many=True).data
        return Response({"items": data})