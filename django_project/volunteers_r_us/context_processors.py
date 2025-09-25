try:
    from .models import Notification

except Exception:
    Notification = None

def notifications_ctx(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated or Notification is None:
        return {"notif_unread": 0, "notif_latest": []}
    qs = Notification.objects.filter(user=request.user).order_by("-created_at")
    return {
        "notif_unread": qs.filter(unread=True).count(),
        "notif_latest": list(qs[:10]),
    }