# requires: pip install djangorestframework
from rest_framework import serializers

SKILL_CHOICES = [("first_aid","First Aid"), ("lifting","Lifting"), ("cpr","CPR")]
LANGUAGE_CHOICES = [("english","English"), ("spanish","Spanish"), ("vietnamese","Vietnamese")]
TIME_BLOCK_CHOICES = [("slot_09_12","09:00-12:00"), ("slot_14_18","14:00-18:00")]

class EventMatchSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    required_skills = serializers.ListField(
        child=serializers.ChoiceField(choices=[v for v,_ in SKILL_CHOICES]),
        allow_empty=True,
    )
    languages = serializers.ListField(
        child=serializers.ChoiceField(choices=[v for v,_ in LANGUAGE_CHOICES]),
        allow_empty=True,
    )
    slots = serializers.IntegerField(min_value=1)
    time_blocks = serializers.ListField(
        child=serializers.ChoiceField(choices=[v for v,_ in TIME_BLOCK_CHOICES]),
        allow_empty=True,
    )
    max_radius_miles = serializers.FloatField(required=False, allow_null=True)
