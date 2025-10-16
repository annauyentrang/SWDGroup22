from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt  # dev-only
from .data import VOLUNTEERS, EVENTS
from .forms import VolunteerForm, EventForm
from .domain import Event
from .logic import volunteer_to_dict, event_to_dict, score, match_volunteers

@require_http_methods(["GET"])
def volunteers_api(_request):
    return JsonResponse({"volunteers": [volunteer_to_dict(v) for v in VOLUNTEERS]})

@require_http_methods(["GET"])
def events_api(_request):
    return JsonResponse({"events": [event_to_dict(e) for e in EVENTS]})

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
            cd["slots"], set(cd["time_blocks"]), cd["max_radius_miles"],
            set(cd.get("requires", [])),
        )

    ranked = match_volunteers(VOLUNTEERS, ev)
    return JsonResponse({
        "event": event_to_dict(ev),
        "matches": [{"volunteer": volunteer_to_dict(v), "score": s} for v, s in ranked],
    })
