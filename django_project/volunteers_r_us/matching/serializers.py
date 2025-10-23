# volunteers_r_us/matching/forms.py
from django import forms

SKILL_CHOICES = [("first_aid","First Aid"), ("lifting","Lifting"), ("cpr","CPR")]
LANGUAGE_CHOICES = [("english","English"), ("spanish","Spanish"), ("vietnamese","Vietnamese")]
TIME_BLOCK_CHOICES = [("slot_09_12","09:00-12:00"), ("slot_14_18","14:00-18:00")]

class EventMatchForm(forms.Form):
    id = forms.IntegerField()
    title = forms.CharField(max_length=200)
    required_skills = forms.MultipleChoiceField(
        choices=[("first_aid","First Aid"), ("lifting","Lifting"), ("cpr","CPR")], required=False
    )
    languages = forms.MultipleChoiceField(
        choices=[("english","English"), ("spanish","Spanish"), ("vietnamese","Vietnamese")], required=False
    )
    slots = forms.IntegerField(min_value=1)
    time_blocks = forms.MultipleChoiceField(
        choices=[("slot_09_12","09:00-12:00"), ("slot_14_18","14:00-18:00")], required=False
    )
    max_radius_miles = forms.FloatField(required=False)

    def clean_max_radius_miles(self):
        v = self.cleaned_data.get("max_radius_miles")
        # treat empty string as None
        return None if v in ("", None) else v

