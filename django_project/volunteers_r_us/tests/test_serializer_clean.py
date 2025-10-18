# django_project/volunteers_r_us/tests/test_serializer_clean.py
from django.test import SimpleTestCase
from ..matching.serializers import EventMatchForm

class TestEventMatchForm(SimpleTestCase):
    def test_max_radius_cleaner_none_and_number(self):
        f1 = EventMatchForm(data={"id":1,"title":"T","required_skills":[],
                                  "languages":["english"],"slots":1,
                                  "time_blocks":[], "max_radius_miles": ""})
        assert f1.is_valid()
        assert f1.cleaned_data["max_radius_miles"] is None

        f2 = EventMatchForm(data={"id":2,"title":"T2","required_skills":[],
                                  "languages":["english"],"slots":1,
                                  "time_blocks":[], "max_radius_miles": "3.5"})
        assert f2.is_valid()
        assert f2.cleaned_data["max_radius_miles"] == 3.5
