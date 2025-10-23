import datetime as dt
import logging
import calendar
from typing import Optional, Union
from django.shortcuts import render, redirect
from django.contrib import messages
from .datastore import VOLUNTEERS, PARTICIPATIONS

logger = logging.getLogger(__name__)

DEFAULT_STATUS_OPTIONS = ["Registered", "Attended", "No-Show", "Cancelled"]
DATE_FMT = "%Y-%m-%d"  # HTML <input type="date">


def _first(qd, *keys, default=""):
    """Returns the first non-empty value from the query dict for the given keys."""
    for k in keys:
        v = qd.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return default

def _get_status_options():
    """Returns a sorted list of unique participation statuses or the default options."""
    # Use .value if it's an Enum; otherwise fall back to str()
    opts = sorted({getattr(p.status, "value", str(p.status)) for p in PARTICIPATIONS.values()})
    return opts or DEFAULT_STATUS_OPTIONS


def _coerce_to_date(d: Union[dt.date, dt.datetime, str, None]) -> Optional[dt.date]:
    """Normalizes a value to a dt.date object without raising exceptions."""
    if d is None:
        return None
    if isinstance(d, dt.date) and not isinstance(d, dt.datetime):
        return d
    if isinstance(d, dt.datetime):
        return d.date()
    if isinstance(d, str):
        # Accept ISO (YYYY-MM-DD), MM/DD/YYYY, or YYYY/MM/DD
        return _parse_qs_date_noexceptions(d)
    return None

def _canon_status(s: Optional[str]) -> str: 
    """Normalizes a status string by case-insensitive matching against available options.""" 
    if not s: 
        return "" 
    s_norm = s.strip().lower() 
    for opt in _get_status_options(): 
        if s_norm == opt.lower(): 
            return opt 
    return ""
# ----------------------- Date helpers (no exceptions) -----------------------

def _safe_date(year: int, month: int, day: int) -> Optional[dt.date]:
    """Constructs a date object safely, validating ranges to avoid exceptions."""
    if not (1 <= month <= 12):
        return None
    dim = calendar.monthrange(year, month)[1]
    if not (1 <= day <= dim):
        return None
    return dt.date(year, month, day)


def _parse_iso_ymd_10(s: str) -> Optional[dt.date]:
    """Parses 'YYYY-MM-DD' from the first 10 characters of a string, without exceptions."""
    if len(s) < 10:
        return None
    if s[4] != "-" or s[7] != "-":
        return None
    year_str, month_str, day_str = s[:4], s[5:7], s[8:10]
    if not (year_str.isdigit() and month_str.isdigit() and day_str.isdigit()):
        return None
    year, month, day = int(year_str), int(month_str), int(day_str)
    return _safe_date(year, month, day)


def _parse_mdy_slash(s: str) -> Optional[dt.date]:
    """Parses 'MM/DD/YYYY' from the first 10 characters of a string, without exceptions."""
    if len(s) < 10:
        return None
    if s[2] != "/" or s[5] != "/":
        return None
    month_str, day_str, year_str = s[:2], s[3:5], s[6:10]
    if not (year_str.isdigit() and month_str.isdigit() and day_str.isdigit()):
        return None
    year, month, day = int(year_str), int(month_str), int(day_str)
    return _safe_date(year, month, day)


def _parse_ymd_slash(s: str) -> Optional[dt.date]:
    """Parses 'YYYY/MM/DD' from the first 10 characters of a string, without exceptions."""
    if len(s) < 10:
        return None
    if s[4] != "/" or s[7] != "/":
        return None
    year_str, month_str, day_str = s[:4], s[5:7], s[8:10]
    if not (year_str.isdigit() and month_str.isdigit() and day_str.isdigit()):
        return None
    year, month, day = int(year_str), int(month_str), int(day_str)
    return _safe_date(year, month, day)


def _parse_qs_date_noexceptions(s: Optional[str]) -> Optional[dt.date]:
    """
    Parses a date string in 'YYYY-MM-DD', 'MM/DD/YYYY', or 'YYYY/MM/DD' formats without exceptions.
    Returns None if parsing fails.
    """
    if not s:
        return None
    s = s.strip()
    d = _parse_iso_ymd_10(s)
    if d:
        return d
    d = _parse_mdy_slash(s)
    if d:
        return d
    d = _parse_ymd_slash(s)
    return d


def _coerce_to_date(d: Union[dt.date, dt.datetime, str, None]) -> Optional[dt.date]:
    """Normalizes a value to a dt.date object without raising exceptions."""
    if d is None:
        return None
    if isinstance(d, dt.date) and not isinstance(d, dt.datetime):
        return d
    if isinstance(d, dt.datetime):
        return d.date()
    if isinstance(d, str):
        return _parse_iso_ymd_10(d)
    return None


# ---------------------------------------------------------------------------

def volunteer_history(request):
    """
    Displays volunteer history based on filter criteria.
    """
    if "reset" in request.GET:
        return redirect(request.path)

    q = request.GET  # QueryDict

    # Accept several common field names from your templates
    volunteer_id = _first(q, "volunteer", "volunteer_id")
    status_filter = _first(q, "status") or ""

    # Accept multiple possible names for the 'from date' field
    from_date_str = _first(q, "from", "from_date", "fromDate", "start", "start_date")
    from_date: Optional[dt.date] = _parse_qs_date_noexceptions(from_date_str)

    canonical_status = _canon_status(status_filter)

    rows = []
    for record in PARTICIPATIONS.values():
        event_date = _coerce_to_date(getattr(record, "event_date", None))
        # Normalize status for Enums or strings
        record_status = getattr(record.status, "value", str(record.status))

        include = True

        if volunteer_id and str(record.volunteer_id) != str(volunteer_id):
            include = False

        if include and canonical_status and record_status.lower() != canonical_status.lower():
            include = False

        # --- KEY FIX: only include rows on/after from_date when provided ---
        if include and from_date is not None:
            if event_date is None or event_date < from_date:
                include = False

        if not include:
            continue

        rows.append({
            "id": record.id,
            "volunteer_id": record.volunteer_id,
            "volunteer_name": record.volunteer_name,
            "event_name": record.event_name,
            "description": record.description,
            "location": record.location,
            "required_skills": record.required_skills,
            "urgency": str(getattr(record.urgency, "value", record.urgency)),
            "event_date": event_date,
            "event_date_iso": event_date.isoformat() if event_date else "",
            "capacity": f"{record.capacity_current} / {record.capacity_total}",
            "languages": record.languages,
            "status": record_status,
            "_sort_date": event_date or dt.date.min,
        })

    rows.sort(key=lambda x: x["_sort_date"])
    for row in rows:
        row.pop("_sort_date", None)

    active_filters = {
        "volunteer": str(volunteer_id) if volunteer_id else "",
        "status": canonical_status,
        "from_date": from_date.isoformat() if from_date else "",
        "date_format_hint": DATE_FMT,
    }

    context = {
        "volunteers": VOLUNTEERS,
        "statuses": _get_status_options(),
        "rows": rows,
        "count": len(rows),
        "filter": active_filters,
    }

    return render(request, "volunteer_history.html", context)