try:
    from .models import Notification

except Exception:
    Notification = None

def notifications(request):
    if request.user.is_authenticated:
        latest = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread_count = latest.filter(unread=True).count()
        return {"notif_latest": latest, "notif_unread": unread_count}
    return {}