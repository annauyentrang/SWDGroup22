from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'home.html')

def login(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')

from django.shortcuts import render, redirect

# volunteers_r_us/views.py
from django.shortcuts import render

def match_volunteer(request):
    # ---- volunteer list (demo) ----
    volunteers = [
        {
            "id": 1, "name": "Alice Nguyen",
            "skills": ["Spanish", "CPR"],
            "languages": ["English", "Spanish"],
            "availability": ["sat_am", "sun_pm"],
            "location_radius_miles": 10,
            "certifications": ["CPR"],
            "constraints": ["No heavy lifting"],
        },
        {
            "id": 2, "name": "Bob Tran",
            "skills": ["Driving", "Lifting"],
            "languages": ["English", "Vietnamese"],
            "availability": ["sun_pm"],
            "location_radius_miles": 15,
            "certifications": ["Background Check"],
            "constraints": [],
        },
    ]

    # events (demo)
    events = [
        {
            "id": 1, "title": "Food Drive",
            "required_skills": ["Food handling", "Spanish"],
            "nice_skills": ["Driving"],
            "slot": "sat_am", "date": "2025-09-27 09:00",
            "location": "Downtown Pantry",
            "capacity_remaining": 5, "min_age": 16, "bg_check": True,
        },
        {
            "id": 2, "title": "Park Cleanup",
            "required_skills": ["Lifting"],
            "nice_skills": [], "slot": "sun_pm", "date": "2025-09-28 14:00",
            "location": "Memorial Park",
            "capacity_remaining": 0, "min_age": 14, "bg_check": False,
        },
        {
            "id": 3, "title": "Blood Donation Desk",
            "required_skills": ["Customer service"],
            "nice_skills": ["CPR"], "slot": "sat_am", "date": "2025-09-27 09:00",
            "location": "City Hall",
            "capacity_remaining": 2, "min_age": 18, "bg_check": False,
        },
    ]

    # selected volunteer id from GET or POST, default first
    sel_vid = request.GET.get("volunteer_id") or request.POST.get("volunteer_id") or str(volunteers[0]["id"])
    volunteer = next(v for v in volunteers if str(v["id"]) == str(sel_vid))

    # scoring
    def score(ev, v):
        vskills = set(v["skills"])
        eskills = set(ev["required_skills"])
        overlap = len(vskills & eskills)
        time_fit = 1 if ev["slot"] in v["availability"] else 0
        return overlap * 10 + time_fit

    suggested = max(events, key=lambda e: score(e, volunteer))

    # selected event (POST or suggested)
    sel_eid = request.POST.get("matched_event") or suggested["id"]
    selected = next(e for e in events if str(e["id"]) == str(sel_eid))

    # insights / warnings
    vskills = set(volunteer["skills"])
    eskills = set(selected["required_skills"])
    overlap = vskills & eskills
    time_fit = selected["slot"] in volunteer["availability"]
    warnings = []
    if selected["capacity_remaining"] <= 0:
        warnings.append("No capacity remaining.")
    missing = eskills - vskills
    if missing:
        warnings.append(f"Missing required skills: {', '.join(sorted(missing))}.")
    if not time_fit:
        warnings.append("Volunteer not available for this time slot.")
    if selected["bg_check"] and "Background Check" not in volunteer["certifications"]:
        warnings.append("Background check required but not on file.")

    match_score = score(selected, volunteer)
    match_reason = f"{len(overlap)} skill match; time fit={time_fit}"

    # save echo (demo only)
    saved, errors = None, []
    if request.method == "POST" and request.POST.get("action"):
        override = request.POST.get("override") == "on"
        override_reason = request.POST.get("override_reason", "").strip()
        if override and not override_reason:
            errors.append("Override reason is required when override is checked.")
        if not errors:
            saved = {
                "volunteer_id": volunteer["id"],
                "event_id": selected["id"],
                "action": request.POST.get("action"),
                "notify": request.POST.get("action") == "assign_notify",
                "override": override,
                "override_reason": override_reason or None,
                "admin_notes": (request.POST.get("admin_notes") or "").strip() or None,
                "match_score": match_score,
                "match_reason": match_reason,
                "warnings": warnings,
            }

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
