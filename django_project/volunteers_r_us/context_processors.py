from .models import Notification

def notifications(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {
            "notif_items": [],
            "notif_unread_count": 0,
        }

    qs = Notification.objects.filter(user=request.user).order_by("-created_at")
    items = list(qs[:10])  # slice first; don't chain filters after this
    # Since there's no 'unread' field in the model, use total count for now
    return {
        "notif_items": items,
        "notif_unread_count": qs.count(),
    }
