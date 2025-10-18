from datetime import datetime, timedelta
from django.test import SimpleTestCase
from volunteers_r_us.matching.logic import time_overlap, matches_event, match_volunteers

class TestLogicBranches(SimpleTestCase):
    def test_time_overlap_none_and_edge(self):
        now = datetime.now()
        A = {"start": now, "end": now + timedelta(hours=1)}
        B = {"start": now + timedelta(hours=2), "end": now + timedelta(hours=3)}
        C = {"start": A["end"], "end": A["end"] + timedelta(minutes=1)}
        assert time_overlap(A, B) is False
        assert time_overlap(A, C) is False

    def test_matches_event_skill_lang_capacity_distance(self):
        v = {"skills":{"cpr"}, "languages":{"english"}, "availability":[], "location":{"lat":0,"lng":0}}
        e_skill = {"required_skills":{"driving"}, "languages":{"english"}, "slots":1, "time_blocks":[],
                   "max_radius_miles":None, "location":{"lat":0,"lng":0}}
        e_lang  = {"required_skills":{"cpr"}, "languages":{"spanish"}, "slots":1, "time_blocks":[],
                   "max_radius_miles":None, "location":{"lat":0,"lng":0}}
        e_full  = {"required_skills":{"cpr"}, "languages":{"english"}, "slots":0, "time_blocks":[],
                   "max_radius_miles":None, "location":{"lat":0,"lng":0}}
        e_far   = {"required_skills":{"cpr"}, "languages":{"english"}, "slots":1, "time_blocks":[],
                   "max_radius_miles":1, "location":{"lat":1.0,"lng":1.0}}
        assert matches_event(v, e_skill) is False
        assert matches_event(v, e_lang)  is False
        assert matches_event(v, e_full)  is False
        assert matches_event(v, e_far)   is False

    def test_match_volunteers_scoring(self):
        vols = [
            {"id":1,"full_name":"A","skills":{"cpr"},"languages":{"english"},"availability":[],"location":{"lat":0,"lng":0}},
            {"id":2,"full_name":"B","skills":{"cpr","lifting"},"languages":{"english"},"availability":[],"location":{"lat":0,"lng":0}},
        ]
        ev = {"required_skills":{"cpr"}, "languages":{"english"}, "slots":1,
              "time_blocks":[], "max_radius_miles":None, "location":{"lat":0,"lng":0}}
        ranked = match_volunteers(vols, ev)
        assert [v["id"] for v,_ in ranked] == [2,1]
