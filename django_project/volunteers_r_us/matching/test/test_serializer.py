from ..serializers import EventMatchSerializer

def test_serializer_rejects_invalid_choices():
    s = EventMatchSerializer(data={
        "id":1,"title":"X",
        "required_skills":["not_a_skill"],
        "languages":["not_a_lang"],
        "slots":5,"time_blocks":[], "max_radius_miles":5
    })
    assert not s.is_valid()
    assert "required_skills" in s.errors and "languages" in s.errors

def test_serializer_accepts_valid_minimal():
    s = EventMatchSerializer(data={
        "id":2,"title":"Ok",
        "required_skills":["first_aid"],
        "languages":["english"],
        "slots":10,"time_blocks":[], "max_radius_miles":10
    })
    assert s.is_valid(), s.errors
