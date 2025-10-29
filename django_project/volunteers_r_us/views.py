from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from types import SimpleNamespace
from django.contrib.auth import get_user_model
from .models import Notification, Skill, Event
from datetime import datetime, date
from datetime import date
from django.shortcuts import render
from .models import Notification
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from io import BytesIO
from datetime import datetime as _dt
from .models import Profile
from .forms import ProfileForm, EventForm, STATE_CHOICES, SKILL_CHOICES
import logging
from django.conf import settings
from .models import VolunteerParticipation as VP
from django.utils.timezone import now
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

#@login_required
# volunteers_r_us/views.py
from django.shortcuts import render

# volunteers_r_us/views.py
from django.shortcuts import render
from .models import Notification

from .matching.data import VOLUNTEERS as VDATA, EVENTS as EDATA
from .matching.logic import score, volunteer_to_dict, event_to_dict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from .models import Assignment

@login_required
def match_volunteer(request):
    # pull from your in-memory demo data
    from .matching.data import VOLUNTEERS as VDATA, EVENTS as EDATA

    def _slot_from_timeblocks(tb):
        return next(iter(tb), "")

    def _vol_to_view(v):
        return {
            "id": v.id,
            "name": v.name,
            "skills": sorted(v.skills),
            "languages": sorted(v.languages),
            "availability": sorted(v.availability),
            "location_radius_miles": getattr(v, "radius_miles", 0),
            "certifications": sorted(getattr(v, "certifications", [])),
            "constraints": sorted(getattr(v, "constraints", [])),
        }

    def _event_to_view(e):
        return {
            "id": e.id,
            "title": e.title,
            "required_skills": sorted(e.required_skills),
            "nice_skills": [],
            "slot": _slot_from_timeblocks(e.time_blocks),
            "date": "TBD",
            "location": "TBD",
            "capacity_remaining": 5,
            "min_age": 0,
            "bg_check": False,
        }

    volunteers = [_vol_to_view(v) for v in VDATA]
    events     = [_event_to_view(e) for e in EDATA]

    # chosen volunteer (GET for initial load, POST preserves hidden input)
    sel_vid = request.GET.get("volunteer_id") or request.POST.get("volunteer_id") or str(volunteers[0]["id"])
    volunteer = next(v for v in volunteers if str(v["id"]) == str(sel_vid))

    # tiny score for suggestion
    def _score(ev, v):
        vskills, eskills = set(v["skills"]), set(ev["required_skills"])
        time_fit = 1 if ev["slot"] in v["availability"] else 0
        return len(vskills & eskills) * 10 + time_fit

    suggested = max(events, key=lambda e: _score(e, volunteer))
    sel_eid   = request.POST.get("matched_event") or suggested["id"]
    selected  = next(e for e in events if str(e["id"]) == str(sel_eid))

    # compute warnings/score for display + persistence
    vskills, eskills = set(volunteer["skills"]), set(selected["required_skills"])
    overlap  = vskills & eskills
    time_fit = selected["slot"] in volunteer["availability"]

    warnings = []
    missing = (eskills - vskills)
    if selected["capacity_remaining"] <= 0:
        warnings.append("No capacity remaining.")
    if missing:
        warnings.append(f"Missing required skills: {', '.join(sorted(missing))}.")
    if not time_fit:
        warnings.append("Volunteer not available for this time slot.")
    if selected["bg_check"] and "Background Check" not in volunteer["certifications"]:
        warnings.append("Background check required but not on file.")

    match_score  = _score(selected, volunteer)
    match_reason = f"{len(overlap)} skill match; time fit={time_fit}"

    saved, errors = None, []
    if request.method == "POST":
        # require reason if override checked
        if request.POST.get("override") == "on" and not (request.POST.get("override_reason") or "").strip():
            errors.append("Override reason is required when override is checked.")

        if not errors:
            action = request.POST.get("action") or "assign"
            notify = (action == "assign_notify")

            # write to DB (create or update single row per volunteer/event)
            assignment, created = Assignment.objects.update_or_create(
                volunteer_id=str(volunteer["id"]),
                event_id=str(selected["id"]),
                defaults={
                    "volunteer_name": volunteer["name"],
                    "event_title": selected["title"],
                    "status": Assignment.ASSIGNED,
                    "notify": notify,
                    "override": (request.POST.get("override") == "on"),
                    "override_reason": (request.POST.get("override_reason") or "").strip(),
                    "admin_notes": (request.POST.get("admin_notes") or "").strip(),
                    "match_score": match_score,
                    "match_reason": match_reason,
                    "warnings": warnings,  # if TextField fallback, json.dumps(warnings)
                    "created_by": request.user,
                },
            )

            # keep 'saved' so your template's success box renders immediately
            saved = {
                "volunteer_id": str(volunteer["id"]),
                "event_id": str(selected["id"]),
                "notify": notify,
                "override": (request.POST.get("override") == "on"),
                "override_reason": (request.POST.get("override_reason") or "").strip(),
                "admin_notes": (request.POST.get("admin_notes") or "").strip(),
                "match_score": match_score,
                "match_reason": match_reason,
                "warnings": warnings,
            }

    ctx = {
        "volunteers": volunteers, "volunteer": volunteer, "events": events,
        "selected": selected, "suggested": suggested, "match_score": match_score,
        "match_reason": match_reason, "warnings": warnings, "saved": saved, "errors": errors,
    }
    return render(request, "match_form.html", ctx)

@login_required
def volunteer_history(request):
    if request.GET.get("reset") == "1":
        return redirect(request.path)

    # Filters from the query string
    volunteer = (request.GET.get("volunteer") or "").strip()  # using volunteer_name as value
    status    = (request.GET.get("status") or "").strip()
    from_str = (request.GET.get("from_date") or "").strip()
    def _parse_date(s):
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return _dt.strptime(s, fmt).date()
            except ValueError:
                pass
        return None
    d_from = _parse_date(from_str)
    # Base queryset: sort by date then name (display order only; no date filtering)
    qs = VP.objects.all()

    if volunteer:
        qs = qs.filter(volunteer_name=volunteer)
    if status:
        qs = qs.filter(status=status)
    if d_from:
        qs = qs.filter(event_date=d_from)
    qs = qs.order_by("event_date", "volunteer_name")

    if request.GET.get("export") == "1":
        try:
            headers = [
            "Volunteer", "Event Name", "Description", "Location",
            "Required Skills", "Urgency", "Event Date",
            "Capacity (current / total)", "Languages", "Status"
            ]
            filename = "volunteer_participation"
            if volunteer:
                filename += f"_{volunteer}"
            if status:
                filename += f"_{status}"
            stamp = now().strftime("%Y%m%d-%H%M%S")
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter
            from openpyxl.styles import Font, Alignment

            wb = Workbook()
            ws = wb.active
            ws.title = "Volunteer Participation"
            ws.append(headers)

            # Apply header style
            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")

            for rec in qs:
                ws.append([
                    rec.volunteer_name,
                    rec.event_name,
                    rec.description or "",
                    rec.location or "",
                    ", ".join([s.strip() for s in (rec.required_skills or "").split(",") if s.strip()]),
                    rec.urgency,
                    rec.event_date.strftime("%Y-%m-%d") if rec.event_date else "",
                    f"{rec.capacity_current} / {rec.capacity_total}",
                    ", ".join([s.strip() for s in (rec.languages or "").split(",") if s.strip()]),
                    rec.status,
                ])

            # Autofit-ish column widths
            for col_idx in range(1, ws.max_column + 1):
                col_letter = get_column_letter(col_idx)
                max_len = max(len(str(c.value or "")) for c in ws[col_letter])
                ws.column_dimensions[col_letter].width = min(50, max(12, max_len + 2))

            # Stream workbook
            bio = BytesIO()
            wb.save(bio)
            bio.seek(0)
            timestamp = now().strftime("%Y%m%d-%H%M%S")
            resp = HttpResponse(
                bio.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            resp["Content-Disposition"] = f'attachment; filename="{filename}_{stamp}.xlsx"'
            return resp

        except ImportError:
            import csv
            from io import StringIO
            sio = StringIO()
            writer = csv.writer(sio)
            writer.writerow(headers)
            for rec in qs:
                writer.writerow([
                    rec.volunteer_name,
                    rec.event_name,
                    rec.description or "",
                    rec.location or "",
                    rec.required_skills,
                    rec.urgency,
                    rec.event_date.strftime("%Y-%m-%d") if rec.event_date else "",
                    f"{rec.capacity_current} / {rec.capacity_total}",
                    rec.languages or "",
                    rec.status,
                ])
            resp = HttpResponse(sio.getvalue(), content_type="text/csv")
            resp["Content-Disposition"] = f'attachment; filename="{filename}_{stamp}.csv"'
            return resp
    # Distinct volunteer names -> objects with id/full_name for your template
    names = list(
        VP.objects.order_by().values_list("volunteer_name", flat=True).distinct()
    )
    volunteers = [SimpleNamespace(id=n, full_name=n) for n in names]

    # Status options (from DB, fallback to defaults)
    statuses = list(
        VP.objects.order_by().values_list("status", flat=True).distinct()
    )
    statuses = sorted([s for s in statuses if s]) or ["Registered", "Attended", "No-Show", "Cancelled"]

    # Shape rows for the template
    rows = []
    for r in qs:
        rows.append({
            "id": r.id,
            "volunteer_id": r.volunteer_name,  # using name as identifier
            "volunteer_name": r.volunteer_name,
            "event_name": r.event_name,
            "description": r.description,
            "location": r.location,
            "required_skills": [s.strip() for s in (r.required_skills or "").split(",") if s.strip()],
            "urgency": r.urgency,
            "event_date": r.event_date,
            "event_date_iso": r.event_date.isoformat() if r.event_date else "",
            "capacity": f"{r.capacity_current} / {r.capacity_total}",
            "languages": [l.strip() for l in (r.languages or "").split(",") if l.strip()],
            "status": r.status,
        })

    return render(
        request,
        "volunteer_history.html",
        {
            "rows": rows,
            "volunteers": volunteers,
            "statuses": statuses,
            "count": len(rows),
            "filter": {  # NOTE: the template we set up earlier expects "filter", not "filters"
                "volunteer": volunteer,
                "status": status,
                "from_date": d_from.isoformat() if d_from else "",
            },
        },
    )

log = logging.getLogger(__name__)
@login_required
def profile_form(request):
    # Try to load existing profile for this user
    log.info("Using DB: %s", settings.DATABASES["default"]["NAME"])
    try:
        profile = getattr(request.user, "profile", None)
    except Profile.DoesNotExist:
        profile = None

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)

        posted_availability = request.POST.getlist("availability[]")  # e.g. ["2025-11-02", ...]
        posted_skills = request.POST.getlist("skills")                # matches <select multiple name="skills">

        if form.is_valid():
            prof = form.save(commit=False)
            prof.user = request.user
            prof.skills = posted_skills
            prof.availability = posted_availability
            prof.save()
            messages.success(request, "Profile saved to the database.")
            return redirect("profile_form")
        else:
            # show what failed in server logs
            log.warning("ProfileForm errors: %s", form.errors)
            messages.error(request, "Please fix the errors below.")
        selected_state = request.POST.get("state") or ""
        selected_skills = set(posted_skills)
        existing_availability = posted_availability
    else:
        # GET: prefill
        form = ProfileForm(instance=profile)
        selected_state = form.initial.get("state", "") if form.initial else ""
        selected_skills = set(profile.skills if profile else [])
        existing_availability = profile.availability if profile else []

    ctx = {
        "form": form,
        "STATE_CHOICES": STATE_CHOICES,
        "SKILL_CHOICES": SKILL_CHOICES,
        "selected_state": selected_state,
        "selected_skills": selected_skills,
        "existing_availability": existing_availability,
    }
    return render(request, "profile_form.html", ctx)

@login_required
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

    ctx = {"form": form, "SKILL_CHOICES": SKILL_CHOICES, "selected_required_skills": selected_required_skills, "selected_urgency": selected_urgency,}
    return render(request, "event_form.html", ctx)

# Send Event Form info to database
def event_form(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save()

            # If the form was submitted via fetch/AJAX, return JSON
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "id": event.id,
                    "name": event.name,
                    "description": event.description,
                    "location": event.location,
                    "urgency": event.urgency,
                    "event_date": event.event_date.isoformat(),
                    # convert M2M queryset → list of dicts
                    "required_skills": list(
                        event.required_skills.values("id", "name")
                    ),
                })

            # Normal HTML POST → redirect
            return redirect("home")
    else:
        form = EventForm()

    return render(request, "event_form.html", {"form": form})