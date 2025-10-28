from django.apps import apps
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch

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

    try:
        url = reverse("event_form")
    except NoReverseMatch:
        url = "/volunteers_r_us/"

    title = f"New event: {event.name}"
    body  = f"{event.location} on {event.event_date}"

    # materialize user ids and de-dupe on (user, title, url, body)
    ids = list(qs.values_list("id", flat=True))
    existing_user_ids = set(
        N().objects.filter(user_id__in=ids, title=title, url=url, body=body)
        .values_list("user_id", flat=True)
    )

    created = 0
    for u in qs:
        if u.id in existing_user_ids:
            continue
        N().objects.create(
            user=u,
            title=title,
            body=body,
            url=url,
            created_at=timezone.now(),
        )
        created += 1

    return created