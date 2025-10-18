# volunteers_r_us/views.py
from __future__ import annotations

from dataclasses import dataclass  # (kept if you later use dataclasses)
from datetime import date, datetime
from typing import Iterable, Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from .forms import (
    LoginForm,
    RegisterForm,
    UserProfileForm,
    EventForm,
    STATE_CHOICES,
    SKILL_CHOICES,
    URGENCY_CHOICES,
)
from .models import Notification

User = get_user_model()

# ---------------------------
# Basic pages & auth
# ---------------------------
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    """
    Renders login form on GET; authenticates on POST using email+password
    against the InMemoryBackend (or whichever backend you configured).
    """
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user = authenticate(request, email=email, password=password)
        if user:
            auth_login(request, user, backend="volunteers_r_us.auth_backends.InMemoryBackend")
            messages.success(request, f"Welcome back, {email}!")
            return redirect(request.GET.get("next") or "home")
        messages.error(request, "Invalid email or password.")
    return render(request, "login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def register(request: HttpRequest) -> HttpResponse:
    """
    Renders register form on GET; creates a user on POST.
    If you’re using a demo in-memory store, uncomment the DEMO_USERS write.
    If you have a real User model, call User.objects.create_user.
    """
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        # If you truly want in-memory demo auth:
        # settings.DEMO_USERS[email] = password

        # Otherwise create a real Django user (recommended if tests expect it):
        if not User.objects.filter(email__iexact=email).exists():
            User.objects.create_user(email=email, password=password)

        messages.success(request, "Account created successfully! You can now log in.")
        return redirect("login")
    return render(request, "register.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponse:
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


# ---------------------------
# Profile & Event forms (server-side validation)
# ---------------------------
@login_required
def profile_form(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UserProfileForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data.copy()
            # store date list as iso strings so it’s JSON-serializable in session
            if "availability" in cleaned:
                cleaned["availability"] = [d.isoformat() for d in cleaned["availability"]]
            request.session["last_profile"] = cleaned
            messages.success(request, "Profile saved (validated on backend).")
            return redirect("profile_form")
        messages.error(request, "Please fix the errors below.")
    else:
        initial = request.session.get("last_profile")
        form = UserProfileForm(initial=initial)

    selected_state = (request.POST.get("state")
                      if request.method == "POST"
                      else (form.initial or {}).get("state"))
    selected_skills = set(request.POST.getlist("skills")) if request.method == "POST" \
                      else set((form.initial or {}).get("skills", []))

    ctx = {
        "form": form,
        "STATE_CHOICES": STATE_CHOICES,
        "SKILL_CHOICES": SKILL_CHOICES,
        "selected_state": selected_state,
        "selected_skills": selected_skills,
    }
    return render(request, "profile_form.html", ctx)


@login_required
def event_form(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data.copy()
            request.session.setdefault("events", [])
            request.session["events"] = request.session["events"] + [cleaned]
            messages.success(request, "Event created (validated on backend).")
            return redirect("event_form")
        messages.error(request, "Please fix the errors below.")
    else:
        form = EventForm()

    selected_required_skills = set(request.POST.getlist("required_skills")) if request.method == "POST" else set()
    selected_urgency = request.POST.get("urgency") if request.method == "POST" else None

    ctx = {
        "form": form,
        "SKILL_CHOICES": SKILL_CHOICES,
        "URGENCY_CHOICES": URGENCY_CHOICES,
        "selected_required_skills": selected_required_skills,
        "selected_urgency": selected_urgency,
    }
    return render(request, "event_form.html", ctx)


# ---------------------------
# Matching demo with notification
# ---------------------------
def match_volunteer(request: HttpRequest) -> HttpResponse:
    volunteers = [
        {"id": 1, "name": "Alice Nguyen", "skills": ["Spanish", "CPR"],
         "languages": ["English", "Spanish"], "availability": ["sat_am", "sun_pm"],
         "location_radius_miles": 10, "certifications": ["CPR"], "constraints": ["No heavy lifting"]},
        {"id": 2, "name": "Bob Tran", "skills": ["Driving", "Lifting"],
         "languages": ["English", "Vietnamese"], "availability": ["sun_pm"],
         "location_radius_miles": 15, "certifications": ["Background Check"], "constraints": []},
    ]
    events = [
        {"id": 1, "title": "Food Drive", "required_skills": ["Food handling", "Spanish"],
         "nice_skills": ["Driving"], "slot": "sat_am", "date": "2025-09-27 09:00",
         "location": "Downtown Pantry", "capacity_remaining": 5, "min_age": 16, "bg_check": True},
        {"id": 2, "title": "Park Cleanup", "required_skills": ["Lifting"],
         "nice_skills": [], "slot": "sun_pm", "date": "2025-09-28 14:00",
         "location": "Memorial Park", "capacity_remaining": 0, "min_age": 14, "bg_check": False},
        {"id": 3, "title": "Blood Donation Desk", "required_skills": ["Customer service"],
         "nice_skills": ["CPR"], "slot": "sat_am", "date": "2025-09-27 09:00",
         "location": "City Hall", "capacity_remaining": 2, "min_age": 18, "bg_check": False},
    ]

    sel_vid = request.GET.get("volunteer_id") or request.POST.get("volunteer_id") or str(volunteers[0]["id"])
    volunteer = next(v for v in volunteers if str(v["id"]) == str(sel_vid))

    def score(ev, v):
        vskills, eskills = set(v["skills"]), set(ev["required_skills"])
        time_fit = 1 if ev["slot"] in v["availability"] else 0
        return len(vskills & eskills) * 10 + time_fit

    suggested = max(events, key=lambda e: score(e, volunteer))
    sel_eid = request.POST.get("matched_event") or suggested["id"]
    selected = next(e for e in events if str(e["id"]) == str(sel_eid))

    vskills, eskills = set(volunteer["skills"]), set(selected["required_skills"])
    overlap = vskills & eskills
    time_fit = selected["slot"] in volunteer["availability"]
    warnings, missing = [], (eskills - vskills)
    if selected["capacity_remaining"] <= 0:
        warnings.append("No capacity remaining.")
    if missing:
        warnings.append(f"Missing required skills: {', '.join(sorted(missing))}.")
    if not time_fit:
        warnings.append("Volunteer not available for this time slot.")
    if selected["bg_check"] and "Background Check" not in volunteer["certifications"]:
        warnings.append("Background check required but not on file.")

    match_score = score(selected, volunteer)
    match_reason = f"{len(overlap)} skill match; time fit={time_fit}"

    saved, errors = None, []

    if request.method == "POST":
        if request.POST.get("override") == "on" and not request.POST.get("override_reason", "").strip():
            errors.append("Override reason is required when override is checked.")

        if not errors:
            saved = {
                "volunteer_id": volunteer["id"],
                "event_id": selected["id"],
                "action": request.POST.get("action"),
                "notify": request.POST.get("action") == "assign_notify",
                "override": request.POST.get("override") == "on",
                "override_reason": (request.POST.get("override_reason") or "").strip() or None,
                "admin_notes": (request.POST.get("admin_notes") or "").strip() or None,
                "match_score": match_score,
                "match_reason": match_reason,
                "warnings": warnings,
            }

            if request.user.is_authenticated:
                Notification.objects.create(
                    user=request.user,
                    message=f"Assigned {volunteer['name']} to {selected['title']}",
                    url=request.path,
                )

    ctx = {
        "volunteers": volunteers,
        "volunteer": volunteer,
        "events": events,
        "selected": selected,
        "suggested": suggested,
        "match_score": match_score,
        "match_reason": match_reason,
        "warnings": warnings,
        "saved": saved,
        "errors": errors,
    }
    return render(request, "match_form.html", ctx)


# ---------------------------
# Volunteer History (filtering)
# ---------------------------
VOLUNTEERS = {
    "1": "Nareh Hovhanesian",
    "2": "Katia Qahwajian",
    "3": "Simon Zhamkochyan",
    "4": "Anglina Samsonyan",
}

HISTORY = [
    {
        "volunteer": "1",
        "volunteer_name": VOLUNTEERS["1"],
        "event_name": "Park Cleanup",
        "event_description": "Neighborhood park litter & brush removal.",
        "location": "Memorial Park, Houston TX",
        "required_skills": ["Lifting", "Driving"],
        "urgency": "High",
        "event_date": date(2025, 9, 28),
        "capacity": "0 / 25",
        "languages": ["English", "Vietnamese"],
        "status": "Registered",
    },
    {
        "volunteer": "2",
        "volunteer_name": VOLUNTEERS["2"],
        "event_name": "Blood Donation Desk",
        "event_description": "Check-in and refreshments table.",
        "location": "Community Center, Suite B",
        "required_skills": ["Customer Service", "Organization"],
        "urgency": "Medium",
        "event_date": date(2025, 10, 5),
        "capacity": "12 / 15",
        "languages": ["English"],
        "status": "Attended",
    },
    {
        "volunteer": "1",
        "volunteer_name": VOLUNTEERS["1"],
        "event_name": "Food Drive Sorting",
        "event_description": "Sort non-perishables; label and stock shelves.",
        "location": "St. Mary’s Hall",
        "required_skills": ["Lifting", "Inventory"],
        "urgency": "Low",
        "event_date": date(2025, 10, 19),
        "capacity": "30 / 40",
        "languages": ["English", "Spanish"],
        "status": "No-Show",
    },
    {
        "volunteer": "4",
        "volunteer_name": VOLUNTEERS["4"],
        "event_name": "Shelter Meal Prep",
        "event_description": "Prep and package warm meals for families.",
        "location": "Hope Shelter Kitchen",
        "required_skills": ["Cooking", "Organization"],
        "urgency": "High",
        "event_date": date(2025, 10, 22),
        "capacity": "8 / 12",
        "languages": ["English"],
        "status": "Cancelled",
    },
]


@login_required
def volunteer_history(request: HttpRequest) -> HttpResponse:
    v = (request.GET.get("volunteer") or "").strip()
    s = (request.GET.get("status") or "").strip()
    f = (request.GET.get("from") or "").strip()
    t = (request.GET.get("to") or "").strip()

    def parse(d: str) -> Optional[date]:
        if not d:
            return None
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            return None

    fdate, tdate = parse(f), parse(t)

    rows = []
    for r in HISTORY:
        if v and r["volunteer"] != v:
            continue
        if s and r["status"] != s:
            continue
        if fdate and r["event_date"] < fdate:
            continue
        if tdate and r["event_date"] > tdate:
            continue
        rows.append(r)

    rows.sort(key=lambda x: x["event_date"], reverse=True)
    volunteers_list = [{"id": k, "name": vname} for k, vname in VOLUNTEERS.items()]

    return render(
        request,
        "volunteer_history.html",
        {
            "rows": rows,
            "volunteers": volunteers_list,
            "filters": {"volunteer": v, "status": s, "from": f, "to": t},
        },
    )
