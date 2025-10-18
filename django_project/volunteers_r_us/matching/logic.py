from math import hypot
from datetime import datetime

def _val(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def _to_dt(x):
    return x if isinstance(x, datetime) else datetime.fromisoformat(x)

def time_overlap(a, b):
    a0, a1 = _to_dt(a["start"]), _to_dt(a["end"])
    b0, b1 = _to_dt(b["start"]), _to_dt(b["end"])
    return not (a1 <= b0 or b1 <= a0)

def matches_event(v, e):
    if not set(_val(e, "required_skills", []))\
            .issubset(set(_val(v, "skills", []))):
        return False
    langs = _val(e, "languages", [])
    if langs and not (set(langs) & set(_val(v, "languages", []))):
        return False
    if _val(e, "slots", 1) <= 0:
        return False
    r = _val(e, "max_radius_miles", None)
    if r is not None:
        V = _val(v, "location", {"lat": 0.0, "lng": 0.0})
        E = _val(e, "location", {"lat": 0.0, "lng": 0.0})
        if hypot(V["lat"] - E["lat"], V["lng"] - E["lng"]) >= r:
            return False
    tbs = _val(e, "time_blocks", [])
    if tbs:
        av = _val(v, "availability", [])
        if not any(time_overlap(tb, a) for tb in tbs for a in av):
            return False
    return True

def score(v, e):
    s = 0
    s += len(set(_val(e, "required_skills", [])) & set(_val(v, "skills", [])))
    s += len(set(_val(e, "languages", [])) & set(_val(v, "languages", [])))
    return float(s)

def match_volunteers(volunteers, event):
    elig = [(v, score(v, event)) for v in volunteers if matches_event(v, event)]
    return sorted(elig, key=lambda t: t[1], reverse=True)

def volunteer_to_dict(v):
    return {
        "id": _val(v, "id"),
        "full_name": _val(v, "full_name") or _val(v, "name"),
        "skills": list(_val(v, "skills", [])),
        "languages": list(_val(v, "languages", [])),
        "location": _val(v, "location", {"lat": 0.0, "lng": 0.0}),
        "availability": list(_val(v, "availability", [])),
    }

def event_to_dict(e):
    return {
        "id": _val(e, "id"),
        "title": _val(e, "title"),
        "required_skills": list(_val(e, "required_skills", [])),
        "languages": list(_val(e, "languages", [])),
        "slots": _val(e, "slots", 0),
        "time_blocks": list(_val(e, "time_blocks", [])),
        "max_radius_miles": _val(e, "max_radius_miles"),
        "location": _val(e, "location", {"lat": 0.0, "lng": 0.0}),
    }
