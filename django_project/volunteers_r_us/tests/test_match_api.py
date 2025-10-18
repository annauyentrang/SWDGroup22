import json
from django.test import TestCase, RequestFactory
from ..matching import views
from ..matching.data import EVENTS

class TestMatchAPI(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_bad_json(self):
        req = self.rf.post("/matching/match/", data="{bad", content_type="application/json")
        r = views.match_api(req)
        assert r.status_code == 400

    def test_unknown_event_id(self):
        req = self.rf.post("/matching/match/", data=json.dumps({"event_id": 999999}), content_type="application/json")
        r = views.match_api(req)
        assert r.status_code == 400

    def test_existing_event_id(self):
        e0 = EVENTS[0]
        eid = e0["id"] if isinstance(e0, dict) else e0.id
        req = self.rf.post("/matching/match/", data=json.dumps({"event_id": eid}), content_type="application/json")
        r = views.match_api(req)
        assert r.status_code == 200
        data = json.loads(r.content)
        assert "matches" in data and "event" in data

    def test_inline_event_payload_ok(self):
        payload = {
            "id": 123, "title": "Clinic",
            "required_skills": ["cpr"], "languages": ["english"],
            "slots": 1, "time_blocks": []
        }
        req = self.rf.post("/matching/match/", data=json.dumps(payload), content_type="application/json")
        r = views.match_api(req)
        assert r.status_code == 200
