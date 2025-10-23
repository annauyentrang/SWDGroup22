from volunteers_r_us.history import views
import types
import datetime as dt
import builtins

import pytest
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage



# ---------- Test utilities ----------

class Obj:
    """Simple attribute bag to mimic your Participation objects."""
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

def _msg_setup(request):
    """
    Attach a working messages backend to the request so
    views.messages.* calls won't error in tests.
    """
    # messages framework requires a session; use dict stub
    setattr(request, "session", {})
    storage = FallbackStorage(request)
    setattr(request, "_messages", storage)


@pytest.fixture
def rf():
    return RequestFactory()

@pytest.fixture
def patch_render(monkeypatch):
    import datetime as dt
    captured = {}

    def serialize(v):
        # dates
        if isinstance(v, dt.date):
            return v.isoformat()
        # simple volunteer-like objects: have id + full_name
        if hasattr(v, "id") and hasattr(v, "full_name"):
            return {"id": v.id, "full_name": v.full_name}
        # lists / dicts (recurse)
        if isinstance(v, list):
            return [serialize(i) for i in v]
        if isinstance(v, dict):
            return {k: serialize(val) for k, val in v.items()}
        # primitives / everything else
        return v

    def fake_render(request, template_name, context):
        captured["template"] = template_name
        captured["context"] = context
        safe = {k: serialize(v) for k, v in context.items()}
        from django.http import JsonResponse
        return JsonResponse(safe)

    from volunteers_r_us.history import views
    monkeypatch.setattr(views, "render", fake_render)
    return captured



@pytest.fixture
def sample_data(monkeypatch):
    """
    Monkeypatch VOLUNTEERS and PARTICIPATIONS in the *views module namespace*.
    We simulate different dates (and years) to stress the month/day filter.
    """
    volunteers = [
        Obj(id=1, full_name="Nareh Hovhanesian"),
        Obj(id=2, full_name="Katia Qahwajian"),
    ]

    # Minimal enum-like with .value to mirror your code path
    class Status:
        def __init__(self, v): self.value = v

    class Urgency:
        def __init__(self, v): self.value = v

    p = {
        101: Obj(
            id=101,
            volunteer_id=1, volunteer_name="Nareh Hovhanesian",
            event_name="Food Drive", description="Pack boxes",
            location="Houston", required_skills=["packing"],
            urgency=Urgency("High"),
            event_date=dt.date(2025, 10, 10),
            capacity_current=5, capacity_total=10,
            languages=["EN"], status=Status("Registered"),
        ),
        102: Obj(
            id=102,
            volunteer_id=1, volunteer_name="Nareh Hovhanesian",
            event_name="Park Cleanup", description="Trash pickup",
            location="Houston", required_skills=["cleanup"],
            urgency=Urgency("Low"),
            event_date=dt.datetime(2024, 10, 22, 8),  # datetime -> date() path
            capacity_current=2, capacity_total=20,
            languages=["EN"], status=Status("Attended"),
        ),
        103: Obj(
            id=103,
            volunteer_id=2, volunteer_name="Katia Qahwajian",
            event_name="Fundraiser", description="Ticketing",
            location="Houston", required_skills=["sales"],
            urgency=Urgency("Medium"),
            event_date="2025-10-25T12:00:00Z",         # str -> 'YYYY-MM-DD...' path
            capacity_current=8, capacity_total=15,
            languages=["EN", "HY"], status=Status("No-Show"),
        ),
        104: Obj(
            id=104,
            volunteer_id=2, volunteer_name="Katia Qahwajian",
            event_name="Blood Drive", description="Front desk",
            location="Houston", required_skills=["desk"],
            urgency=Urgency("High"),
            event_date=None,                           # None path
            capacity_current=1, capacity_total=30,
            languages=["EN"], status=Status("Cancelled"),
        ),
    }

    monkeypatch.setattr(views, "VOLUNTEERS", volunteers, raising=True)
    monkeypatch.setattr(views, "PARTICIPATIONS", p, raising=True)

    return {"VOLUNTEERS": volunteers, "PARTICIPATIONS": p}


# ---------- Helper function tests ----------

def test__first():
    qd = {"a": "  ", "b": "hello", "c": "world"}
    assert views._first(qd, "a", "b") == "hello"
    assert views._first(qd, "x", "y", default="fallback") == "fallback"


def test__canon_status(sample_data):
    assert views._canon_status(" registered ") == "Registered"
    assert views._canon_status("ATTENDED") == "Attended"
    assert views._canon_status("unknown") == ""     # not found → empty
    assert views._canon_status(None) == ""


def test__coerce_to_date_variants():
    today = dt.date(2025, 10, 16)
    assert views._coerce_to_date(today) == today
    assert views._coerce_to_date(dt.datetime(2025, 10, 16, 12, 0)).isoformat() == "2025-10-16"
    assert views._coerce_to_date("2025-10-16T12:00:00Z").isoformat() == "2025-10-16"
    assert views._coerce_to_date("bad") is None
    assert views._coerce_to_date(None) is None


# ---------- View tests ----------

def test_view_no_filters_lists_sorted(rf, patch_render, sample_data):
    req = rf.get("/history/")
    _msg_setup(req)
    views.volunteer_history(req)

    ctx = patch_render["context"]
    rows = ctx["rows"]

    # Check we have all 4 rows
    assert ctx["count"] == 4

    # Dates list (may include None as first element)
    dates = [r["event_date"] for r in rows]

    # The first should be the None date (sorted via date.min)
    assert dates[0] is None

    # The remaining should be in ascending order
    assert dates[1:] == [
        dt.date(2024, 10, 22),
        dt.date(2025, 10, 10),
        dt.date(2025, 10, 25),
    ]

def test_view_filter_by_volunteer(rf, patch_render, sample_data):
    req = rf.get("/history/?volunteer=1")
    _msg_setup(req)
    resp = views.volunteer_history(req)
    ctx = patch_render["context"]
    assert ctx["count"] == 2
    assert all(r["volunteer_id"] == 1 for r in ctx["rows"])

def test_view_filter_by_status_case_insensitive(rf, patch_render, sample_data):
    req = rf.get("/history/?status=attended")
    _msg_setup(req)
    resp = views.volunteer_history(req)
    ctx = patch_render["context"]
    assert ctx["count"] == 1
    assert ctx["rows"][0]["status"].lower() == "attended"

def test_view_filter_by_from_date_full_date_iso(rf, patch_render, sample_data):
    # full-date filter (ISO)
    req = rf.get("/history/?from_date=2025-10-22")
    _msg_setup(req)
    views.volunteer_history(req)

    ctx = patch_render["context"]
    dates = [r["event_date"] for r in ctx["rows"]]

    # Only 2025-10-25 is >= 2025-10-22 (None excluded)
    assert dates == [dt.date(2025, 10, 25)]

def test_view_filter_by_from_date_full_date_mmddyyyy(rf, patch_render, sample_data):
    # full-date filter (UI format)
    req = rf.get("/history/?from_date=10/22/2025")
    _msg_setup(req)
    views.volunteer_history(req)

    ctx = patch_render["context"]
    dates = [r["event_date"] for r in ctx["rows"]]

    # Same result as ISO: only 2025-10-25
    assert dates == [dt.date(2025, 10, 25)]

def test_view_invalid_from_date_is_ignored(rf, patch_render, sample_data):
    # invalid format → no filter is applied; no error messages are queued by this view
    req = rf.get("/history/?from_date=not-a-date")
    _msg_setup(req)
    views.volunteer_history(req)

    ctx = patch_render["context"]
    assert ctx["count"] == 4

def test_view_reset_redirects(rf, sample_data):
    req = rf.get("/history/?reset=1&from_date=2025-10-22")
    _msg_setup(req)
    resp = views.volunteer_history(req)
    # Redirect to same path (clears query)
    assert resp.status_code in (301, 302)
    assert resp.headers["Location"].endswith("/history/")

def test_view_context_has_filter_object(rf, patch_render, sample_data):
    req = rf.get("/history/?volunteer=2&status=No-Show&from_date=2025-10-22")
    _msg_setup(req)
    views.volunteer_history(req)
    f = patch_render["context"]["filter"]
    assert f["volunteer"] == "2"
    assert f["status"] == "No-Show"
    assert f["from_date"] == "2025-10-22"
    assert f["date_format_hint"] == views.DATE_FMT