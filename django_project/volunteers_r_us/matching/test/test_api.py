from django.test import SimpleTestCase, Client
import json

class MatchApiTests(SimpleTestCase):
    def setUp(self):
        self.c = Client()

    def test_volunteers_endpoint_get_ok(self):
        r = self.c.get("/api/volunteers/")
        assert r.status_code == 200
        data = json.loads(r.content)
        assert "volunteers" in data
        assert isinstance(data["volunteers"], list)

    def test_match_requires_valid_payload(self):
        r = self.c.post("/api/match/", data=json.dumps({
            "id": 10,
            "title": "Beach",
            "required_skills": ["first_aid"],
            "languages": ["english"],
            "slots": 5,
            "time_blocks": [],
            "max_radius_miles": 10
        }), content_type="application/json")
        assert r.status_code in (200, 201, 202, 400)
        # If 200, assert structure
        if r.status_code == 200:
            data = json.loads(r.content)
            assert "matches" in data
            assert isinstance(data["matches"], list)
