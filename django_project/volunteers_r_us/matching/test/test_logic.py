from datetime import datetime
from ..logic import matches_event, time_overlap

V = {
  "skills": ["first_aid","lifting"],
  "languages": ["english","spanish"],
  "location": {"lat":0.0,"lng":0.0},
  "availability":[
    {"start": datetime(2025,10,20,9), "end": datetime(2025,10,20,12)},
    {"start": datetime(2025,10,21,14), "end": datetime(2025,10,21,18)},
  ],
}

def E(**kw):
    e = {
      "required_skills": [], "languages": [], "slots": 5, "max_radius_miles": 10,
      "location":{"lat":0.0,"lng":0.0}, "time_blocks":[]
    }
    e.update(kw); return e

def test_skill_subset_required():
    assert matches_event(V, E(required_skills=["first_aid"])) is True
    assert matches_event(V, E(required_skills=["first_aid","cpr"])) is False

def test_language_intersection():
    assert matches_event(V, E(languages=["english"])) is True
    assert matches_event(V, E(languages=["vietnamese"])) is False

def test_slots_positive():
    assert matches_event(V, E(slots=1)) is True
    assert matches_event(V, E(slots=0)) is False

def test_radius_filter():
    assert matches_event(V, E(max_radius_miles=0.5, location={"lat":0.3,"lng":0.4})) is False
    assert matches_event(V, E(max_radius_miles=1.0, location={"lat":0.3,"lng":0.4})) is True

def test_time_overlap_required():
    tb = [{"start": datetime(2025,10,20,10), "end": datetime(2025,10,20,11)}]
    assert matches_event(V, E(time_blocks=tb)) is True
    tb2 = [{"start": datetime(2025,10,20,12), "end": datetime(2025,10,20,13)}]  # ends exactly at 12
    assert matches_event(V, E(time_blocks=tb2)) is False  # edge: end==start → no overlap

def test_multiple_time_blocks_any_overlap_ok():
    tbs = [
      {"start": datetime(2025,10,20,7), "end": datetime(2025,10,20,8)},
      {"start": datetime(2025,10,21,16), "end": datetime(2025,10,21,17)},
    ]
    assert matches_event(V, E(time_blocks=tbs)) is True
