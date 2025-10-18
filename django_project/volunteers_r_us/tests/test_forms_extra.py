from django.test import SimpleTestCase
from ..matching.forms import VolunteerForm

class TestVolunteerFormExtra(SimpleTestCase):
    def test_invalid_language_and_blank_trim(self):
        bad = {"id":1,"name":"  ","skills":["CPR"],"languages":["??"],"availability":[],
               "radius_miles":1,"certifications":[],"constraints":[]}
        f = VolunteerForm(data=bad)
        assert not f.is_valid()
        assert "name" in f.errors or "languages" in f.errors
