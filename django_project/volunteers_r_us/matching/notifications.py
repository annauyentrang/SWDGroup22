# volunteers_r_us/matching/notifications.py
from django.apps import apps
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.urls import reverse

def N():
    return apps.get_model("notify", "Notification")

def notify_candidates_for_event(event):
    req = list(event.required_skills.values_list("id", flat=True))
    if not req:
        return 0

    U = get_user_model()
    qs = (
        U.objects.filter(vol_profile__skills__in=req)
        .annotate(match_count=Count("vol_profile__skills", distinct=True))
        .filter(match_count=len(req))
        .distinct()
    )

    created = 0
    for u in qs:
        N().objects.create(
            user=u,
            title=f"New event: {event.name}",
            body=f"{event.location} on {event.event_date} (urgency {event.get_urgency_display()})",
            url="#",
            created_at=timezone.now(),
        )
        created += 1
    return created

def create_match_notification(user, event):
    N().objects.create(
        user=user,
        title=f"Matched to {event.name}",
        body=f"{getattr(event, 'event_date', '')}",
        url=reverse("event_detail", args=[event.id]) if getattr(event, "id", None) else "",
        created_at=timezone.now(),
    )
