from django.shortcuts import render

# Create your views here.
from typing import List, Tuple
from .domain import Volunteer, Event
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from .data import VOLUNTEERS, EVENTS
from .forms import VolunteerForm, EventForm

# bypass CRSF for testing
from django.views.decorators.csrf import csrf_exempt

# put near top of matching/views.py
def volunteer_dict(v):
    return {
        "id": v.id,
        "name": v.name,
        "skills": sorted(v.skills),
        "languages": sorted(v.languages),
        "availability": sorted(v.availability),
        "radius_miles": v.radius_miles,
        "certifications": sorted(v.certifications),
        "constraints": sorted(v.constraints),
    }

def event_dict(e):
    return {
        "id": e.id,
        "title": e.title,
        "required_skills": sorted(e.required_skills),
        "languages": sorted(e.languages),
        "slots": e.slots,
        "time_blocks": sorted(e.time_blocks),
        "max_radius_miles": e.max_radius_miles,
        "requires": sorted(e.requires),
    }


def score(vol: Volunteer, ev: Event) -> int:
    s = 0
    s += len(vol.skills & ev.required_skills) * 3
    s += len(vol.languages & ev.languages) * 2
    s += 2 if len(vol.availability & ev.time_blocks) else 0
    s += 1 if vol.radius_miles <= ev.max_radius_miles else -5
    if ev.requires - vol.certifications:
        s -= 100  # hard fail
    if "No heavy lifting" in vol.constraints and "Lifting" in ev.required_skills:
        s -= 100  # hard fail
    return s

def match_volunteers(vols: List[Volunteer], ev: Event, k: int=None) -> List[Tuple[Volunteer,int]]:
    ranked = sorted(((v, score(v, ev)) for v in vols), key=lambda x: x[1], reverse=True)
    ranked = [pair for pair in ranked if pair[1] > 0]
    return ranked[: (k or ev.slots)]

@require_http_methods(["GET"])
def volunteers_api(_request):
    return JsonResponse({"volunteers": [volunteer_dict(v) for v in VOLUNTEERS]})

@require_http_methods(["GET"])
def events_api(_request):
    return JsonResponse({"events": [event_dict(e) for e in EVENTS]})


@csrf_exempt
@require_http_methods(["POST"])
def validate_volunteer(request):
    data = json.loads(request.body or "{}")
    f = VolunteerForm(data)
    if not f.is_valid():
        return JsonResponse({"ok": False, "errors": f.errors}, status=400)
    return JsonResponse({"ok": True})

@csrf_exempt
@require_http_methods(["POST"])
def validate_event(request):
    data = json.loads(request.body or "{}")
    f = EventForm(data)
    if not f.is_valid():
        return JsonResponse({"ok": False, "errors": f.errors}, status=400)
    return JsonResponse({"ok": True})

@csrf_exempt
@require_http_methods(["POST"])
def match_api(request):
    data = json.loads(request.body or "{}")
    if "event_id" in data:
        ev = next((e for e in EVENTS if e.id == data["event_id"]), None)
        if not ev:
            return HttpResponseBadRequest("Unknown event_id")
    else:
        f = EventForm(data)
        if not f.is_valid():
            return JsonResponse({"ok": False, "errors": f.errors}, status=400)
        cd = f.cleaned_data
        ev = Event(
            cd["id"], cd["title"], set(cd["required_skills"]), set(cd["languages"]),
            cd["slots"], set(cd["time_blocks"]), cd["max_radius_miles"], set(cd.get("requires", []))
        )
    ranked = match_volunteers(VOLUNTEERS, ev)

    return JsonResponse({
        "event": event_dict(ev),
        "matches": [{"volunteer": volunteer_dict(v), "score": s} for v, s in ranked],
    })