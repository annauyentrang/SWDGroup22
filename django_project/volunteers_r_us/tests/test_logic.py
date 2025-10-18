from datetime import datetime, timedelta
from django.test import SimpleTestCase
from ..matching.logic import time_overlap, volunteer_to_dict, event_to_dict

class TestLogic(SimpleTestCase):
    def test_time_overlap_true_and_edge_false(self):
        now = datetime.now()
        a = {"start": now, "end": now + timedelta(hours=1)}
        b = {"start": now + timedelta(minutes=30), "end": now + timedelta(hours=2)}
        c = {"start": now + timedelta(hours=1), "end": now + timedelta(hours=2)}
        assert time_overlap(a, b) is True
        assert time_overlap(a, c) is False  # edge: a1 == c0

    def test_helpers_to_dict(self):
        v = {"id": 1, "name": "A", "skills": {"CPR"}, "languages": {"English"}, "availability": []}
        e = {"id": 2, "title": "T", "required_skills": {"CPR"}, "languages": {"English"},
             "slots": 1, "time_blocks": [], "max_radius_miles": 10, "location": {"lat":0.0,"lng":0.0}}
        vd = volunteer_to_dict(v)
        ed = event_to_dict(e)
        assert vd["id"] == 1 and "skills" in vd and isinstance(vd["skills"], list)
        assert ed["id"] == 2 and ed["title"] == "T" and isinstance(ed["required_skills"], list)
