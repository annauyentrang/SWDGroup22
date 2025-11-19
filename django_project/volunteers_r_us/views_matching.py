from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required


from .models import Event, Profile, Skill, Assignment
from .choices import SKILL_CHOICES
from notify.models import Notification

_LABEL_TO_CODE = {label: code for code, label in SKILL_CHOICES}
_CODE_TO_LABEL = {code: label for code, label in SKILL_CHOICES}

def _event_required_codes(event):
    labels = list(event.required_skills.values_list("name", flat=True))
    return [ _LABEL_TO_CODE.get(lbl) for lbl in labels if _LABEL_TO_CODE.get(lbl) ]

def _available_on(profile, event):
    return bool(profile.availability) and event.event_date.isoformat() in profile.availability

def _skill_overlap(profile, required_codes):
    if not required_codes:
        return True
    return bool(set(profile.skills or []).intersection(required_codes))

@login_required
@staff_member_required
def matching_page(request):
    # Pull everything the template needs
    volunteers = (
        Profile.objects.select_related("user")
        .only("id", "full_name", "city", "state", "skills", "availability", "user__email")
        .order_by("full_name", "user__email")
    )
    events = (
        Event.objects.prefetch_related("required_skills")
        .only("id", "name", "location", "urgency", "event_date")
        .order_by("event_date", "name")
    )

    # Optional: when a volunteer is preselected (e.g., after POST redirect)
    selected_volunteer_id = request.GET.get("volunteer_id")
    selected_event_id = request.GET.get("event_id")

    ctx = {
        "volunteers": volunteers,
        "events": events,
        "selected_volunteer_id": int(selected_volunteer_id) if selected_volunteer_id else None,
        "selected_event_id": int(selected_event_id) if selected_event_id else None,
    }
    return render(request, "matching/match_form.html", ctx)   # or matching/matching_page.html


@login_required
@transaction.atomic
def assign_volunteer(request):
    if request.method != "POST":
        return redirect("match_volunteer")

    event_id = request.POST.get("event_id")
    profile_id = request.POST.get("volunteer_id")   # NOTE: we use Profile.id coming from the <select>

    event = get_object_or_404(Event, pk=event_id)
    profile = get_object_or_404(Profile, pk=profile_id)

    # Persist the assignment (one row per user+event)
    assign, created = Assignment.objects.get_or_create(
        volunteer=profile.user,           # <- FK to AUTH_USER
        event=event,
        defaults={"status": Assignment.ASSIGNED},
    )
    if not created:
        assign.status = Assignment.ASSIGNED
        assign.save(update_fields=["status"])




    # In-app notification (notify app)
    msg = f"You’ve been matched to '{event.name}' on {event.event_date} at {event.location}."
    Notification.objects.create(
        user=profile.user,
        title=f"Matched: {event.name}",
        body=msg,
        url="",   # optional deep link
    )

    # Email (console backend in dev)
    send_mail(
        subject=f"[Volunteer Match] {event.name}",
        message=f"Hi {profile.full_name or profile.user.email},\n\n{msg}\n\nThank you for volunteering!",
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
        recipient_list=[profile.user.email],
        fail_silently=True,
    )

    messages.success(request, f"{profile.full_name or profile.user.email} assigned and notified.")
    # Redirect back with selections preserved
    return redirect(f"/volunteers_r_us/matching/?volunteer_id={profile.id}&event_id={event.id}")