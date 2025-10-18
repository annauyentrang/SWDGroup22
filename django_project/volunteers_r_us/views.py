from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from .models import Notification

from datetime import datetime, date
from datetime import date
from django.shortcuts import render
from django.shortcuts import render
from .models import Notification
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import UserProfileForm, EventForm, STATE_CHOICES, SKILL_CHOICES, URGENCY_CHOICES

User = get_user_model()

def home(request):
    return render(request, 'home.html')

def login_view(request):
    # Renders form on GET; authenticates on POST
    ctx = {}
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        # Basic field validations (Assignment requirement)
        errors = []
        if not email:
            errors.append("Email is required.")
        if not password:
            errors.append("Password is required.")
        if errors:
            ctx["info"] = " ".join(errors)
            return render(request, "login.html", ctx)

        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect(request.GET.get("next") or "home")
        ctx["info"] = "Invalid email or password."
    return render(request, "login.html", ctx)

def register_view(request):
    # Renders form on GET; creates user on POST
    ctx = {}
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm", "")

        # Server-side validations (required fields, types/length)
        errors = []
        if not email:
            errors.append("Email is required.")
        if not password:
            errors.append("Password is required.")
        if password and len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords must match.")
        if User.objects.filter(email__iexact=email).exists():
            errors.append("An account with that email already exists.")

        # Run Django’s password validators too
        if password:
            try:
                validate_password(password)
            except ValidationError as ve:
                errors.extend(ve.messages)

        if errors:
            ctx["info"] = " ".join(errors)
            return render(request, "register.html", ctx)

        # Create user and redirect to login
        User.objects.create_user(email=email, password=password)
        ctx["info"] = "Account created. Please sign in."
        return redirect("login")

    return render(request, "register.html", ctx)

def logout_view(request):
    auth_logout(request)
    return redirect("home")

@login_required
def profile_form(request):
    return render(request, "profile_form.html")

@login_required
def event_form(request):
    return render(request, "event_form.html")

@login_required
# volunteers_r_us/views.py
from django.shortcuts import render

# volunteers_r_us/views.py
from django.shortcuts import render
from .models import Notification

from matching.data import VOLUNTEERS as VDATA, EVENTS as EDATA
from matching.logic import score, volunteer_to_dict, event_to_dict


def match_volunteer(request):
    # map backend dataclasses -> the fields your template expects
    def _slot_from_timeblocks(tb): return next(iter(tb), "")
    def _vol_to_view(v):
        return {
            "id": v.id,
            "name": v.name,
            "skills": sorted(v.skills),
            "languages": sorted(v.languages),
            "availability": sorted(v.availability),
            "location_radius_miles": v.radius_miles,
            "certifications": sorted(v.certifications),
            "constraints": sorted(v.constraints),
        }
    def _event_to_view(e):
        return {
            "id": e.id,
            "title": e.title,
            "required_skills": sorted(e.required_skills),
            "nice_skills": [],                     # stub
            "slot": _slot_from_timeblocks(e.time_blocks),
            "date": "TBD",                         # stub
            "location": "TBD",                     # stub
            "capacity_remaining": 5,               # stub
            "min_age": 0,                          # stub
            "bg_check": False,                     # stub
        }

    volunteers = [_vol_to_view(v) for v in VDATA]
    events = [_event_to_view(e) for e in EDATA]

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
    if selected["capacity_remaining"] <= 0: warnings.append("No capacity remaining.")
    if missing: warnings.append(f"Missing required skills: {', '.join(sorted(missing))}.")
    if not time_fit: warnings.append("Volunteer not available for this time slot.")
    if selected["bg_check"] and "Background Check" not in volunteer["certifications"]:
        warnings.append("Background check required but not on file.")

    match_score = score(selected, volunteer)
    match_reason = f"{len(overlap)} skill match; time fit={time_fit}"

    saved, errors = None, []
    if request.method == "POST":
        if request.POST.get("override") == "on" and not (request.POST.get("override_reason") or "").strip():
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
            # Notification Model
            # if request.user.is_authenticated:
            #     Notification.objects.create(
            #         user=request.user,
            #         message=f"Assigned {volunteer['name']} to {selected['title']}",
            #         url=request.path,
            #     )

    ctx = {
        "volunteers": volunteers, "volunteer": volunteer, "events": events,
        "selected": selected, "suggested": suggested, "match_score": match_score,
        "match_reason": match_reason, "warnings": warnings, "saved": saved, "errors": errors,
    }
    return render(request, "match_form.html", ctx)

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
def volunteer_history(request):
    v = (request.GET.get("volunteer") or "").strip()
    s = (request.GET.get("status") or "").strip()
    f = (request.GET.get("from") or "").strip()
    t = (request.GET.get("to") or "").strip()

    def parse(d: str):
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
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

def profile_form(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data.copy()
            cleaned["availability"] = [d.isoformat() for d in cleaned["availability"]]
            # Persist later via DB; for now store in session
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


    ctx = {"form": form, "STATE_CHOICES": STATE_CHOICES, "SKILL_CHOICES": SKILL_CHOICES, "selected_state": selected_state,
        "selected_skills": selected_skills,}
    return render(request, "profile_form.html", ctx)

def event_form(request):
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

    ctx = {"form": form, "SKILL_CHOICES": SKILL_CHOICES, "URGENCY_CHOICES": URGENCY_CHOICES, "selected_required_skills": selected_required_skills, "selected_urgency": selected_urgency,}
    return render(request, "event_form.html", ctx)