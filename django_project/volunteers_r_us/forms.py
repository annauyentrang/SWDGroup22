from datetime import date
from django import forms
from django.core.validators import RegexValidator

STATE_CHOICES = [(s, s) for s in [
    "AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA",
    "ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR",
    "PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
]]

SKILL_CHOICES = [
    ("first_aid", "First Aid / CPR"),
    ("teaching", "Teaching / Tutoring"),
    ("childcare", "Childcare"),
    ("elderly_care", "Elderly Care"),
    ("event_support", "Event Setup / Cleanup"),
    ("cooking", "Cooking & Meal Prep"),
    ("driving", "Driving / Transport"),
    ("it_support", "IT Support"),
    ("graphic_design", "Graphic Design"),
    ("social_media", "Social Media & Marketing"),
    ("translation", "Translation / Interpretation"),
    ("fundraising", "Fundraising"),
    ("photography", "Photography / Videography"),
    ("environment", "Environmental Conservation"),
    ("disaster_relief", "Disaster Relief"),
]

URGENCY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("critical", "Critical"),
]

zip_validator = RegexValidator(
    regex=r"^\d{5}(-?\d{4})?$",
    message="Enter a 5-digit ZIP or 9-digit ZIP (with or without hyphen)."
)

class UserProfileForm(forms.Form):
    full_name = forms.CharField(max_length=50, required=True)
    address1 = forms.CharField(max_length=100, required=True)
    address2 = forms.CharField(max_length=100, required=False)
    city = forms.CharField(max_length=100, required=True)
    state = forms.ChoiceField(choices=STATE_CHOICES, required=True)
    zipcode = forms.CharField(max_length=9, required=True, validators=[zip_validator])
    skills = forms.MultipleChoiceField(choices=SKILL_CHOICES, required=True)
    preferences = forms.CharField(widget=forms.Textarea, required=False)
    availability = forms.Field(required=True)  # we parse availability[] manually

    def clean_availability(self):
        raw_list = self.data.getlist("availability[]") or self.data.getlist("availability") or []
        if not raw_list:
            raise forms.ValidationError("Please add at least one availability date.")
        parsed = []
        for s in raw_list:
            try:
                parsed.append(date.fromisoformat(s))
            except Exception:
                raise forms.ValidationError(f"Invalid date: {s}")
        return parsed

class EventForm(forms.Form):
    event_name = forms.CharField(max_length=100, required=True)
    event_description = forms.CharField(widget=forms.Textarea, required=True)
    location = forms.CharField(widget=forms.Textarea, required=True)
    required_skills = forms.MultipleChoiceField(choices=SKILL_CHOICES, required=True)
    urgency = forms.ChoiceField(choices=URGENCY_CHOICES, required=True)
    event_date = forms.DateField(required=True, input_formats=["%Y-%m-%d"])