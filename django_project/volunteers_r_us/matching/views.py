from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .data import VOLUNTEERS, EVENTS
from .logic import matches_event, match_volunteers, volunteer_to_dict, event_to_dict
from .forms import VolunteerForm, EventForm
from .domain import Event  # if you really need this class; otherwise keep events as dicts

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
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    # Resolve event payload -> dict
    if "event_id" in data:
        # EVENTS may contain objects or dicts
        ev = next(
            (
                e for e in EVENTS
                if (getattr(e, "id", None) == data["event_id"])
                or (isinstance(e, dict) and e.get("id") == data["event_id"])
            ),
            None,
        )
        if ev is None:
            return HttpResponseBadRequest("Unknown event_id")
        ev_dict = event_to_dict(ev)  # normalize for matching + response
    else:
        f = EventForm(data)
        if not f.is_valid():
            return JsonResponse({"ok": False, "errors": f.errors}, status=400)
        ev_dict = f.cleaned_data

    ranked = match_volunteers(VOLUNTEERS, ev_dict)
    return JsonResponse(
        {
            "event": event_to_dict(ev_dict),
            "matches": [
                {"volunteer": volunteer_to_dict(v), "score": s} for v, s in ranked
            ],
        }
    )
