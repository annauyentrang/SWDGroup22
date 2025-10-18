import json
from django.test import TestCase, RequestFactory
from ..matching import views

class TestViews(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_volunteers_and_events_endpoints(self):
        r1 = views.volunteers_api(self.rf.get("/matching/volunteers/"))
        r2 = views.events_api(self.rf.get("/matching/events/"))
        assert r1.status_code == 200 and "volunteers" in json.loads(r1.content)
        assert r2.status_code == 200 and "events" in json.loads(r2.content)

    def test_validate_volunteer_bad_and_ok(self):
        bad = {"id": 1, "name": " ", "skills": ["CPR"], "languages": ["English"],
               "availability": ["sat_am"], "radius_miles": -1, "certifications": [], "constraints": []}
        ok  = {"id": 2, "name": "Ada", "skills": ["CPR"], "languages": ["English"],
               "availability": ["sat_am"], "radius_miles": 5, "certifications": [], "constraints": []}

        req_bad = self.rf.post("/matching/validate/volunteer/", data=json.dumps(bad), content_type="application/json")
        req_ok  = self.rf.post("/matching/validate/volunteer/", data=json.dumps(ok),  content_type="application/json")

        resp_bad = views.validate_volunteer(req_bad)
        resp_ok  = views.validate_volunteer(req_ok)

        assert resp_bad.status_code == 400
        assert json.loads(resp_ok.content)["ok"] is True

    def test_validate_event_title_and_ok(self):
        bad = {"id": 10, "title": "x", "required_skills": [], "languages": ["English"],
               "slots": 0, "time_blocks": ["sat_am"], "max_radius_miles": 10, "requires": []}
        ok  = {"id": 11, "title": "Health Fair", "required_skills": ["CPR"], "languages": ["English"],
               "slots": 1, "time_blocks": ["sat_am"], "max_radius_miles": 10, "requires": []}

        rb = self.rf.post("/matching/validate/event/", data=json.dumps(bad), content_type="application/json")
        ro = self.rf.post("/matching/validate/event/", data=json.dumps(ok),  content_type="application/json")

        eb = views.validate_event(rb)
        eo = views.validate_event(ro)
        assert eb.status_code == 400 and "errors" in json.loads(eb.content)
        assert json.loads(eo.content)["ok"] is True


def test_match_api_by_existing_and_unknown_id(self):
    e0 = EVENTS[0]
    eid = e0["id"] if isinstance(e0, dict) else e0.id  # no eager eval

    r_ok = self.rf.post("/matching/match/", data=json.dumps({"event_id": eid}),
                        content_type="application/json")
    r_bad = self.rf.post("/matching/match/", data=json.dumps({"event_id": 999999}),
                         content_type="application/json")

    resp_ok = views.match_api(r_ok)
    resp_bad = views.match_api(r_bad)

    assert resp_ok.status_code == 200 and "matches" in json.loads(resp_ok.content)
    assert resp_bad.status_code == 400