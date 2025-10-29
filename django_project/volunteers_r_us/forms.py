from datetime import date
from django import forms
from django.core.validators import RegexValidator
from .models import Profile, Skill, Event
from .choices import STATE_CHOICES, SKILL_CHOICES


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

class ProfileForm(forms.ModelForm):
    # Rendered as <select multiple>; we’ll set the list on save()
    skills = forms.MultipleChoiceField(choices=SKILL_CHOICES, required=True)

    class Meta:
        model = Profile
        fields = [
            "full_name", "address1", "address2",
            "city", "state", "zipcode",
            "preferences",
            # NOTE: availability is handled as hidden inputs “availability[]”
        ]
        widgets = {
            "state": forms.Select(choices=STATE_CHOICES),
        }

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

class EventForm(forms.ModelForm):
    required_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(), required=False
    )
    class Meta:
        model = Event
        fields = ["name", "description", "location", "required_skills", "urgency", "event_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "location": forms.Textarea(attrs={"rows": 2}),
            "event_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "name": "Event Name",
            "description": "Event Description",
            "required_skills": "Required Skills",
            "event_date": "Event Date",
        }