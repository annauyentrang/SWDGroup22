from __future__ import annotations
from django import forms
# app/forms.py

from datetime import date
from .domain import Urgency, ParticipationStatus
from .validators import (
    require, max_len, non_negative_int, positive_int, list_of_strings, capacity_ok,
    MAX_LEN_SHORT, MAX_LEN_LONG
)
HISTORY_STATUS_CHOICES = [
    ("", "Any"),
    ("Registered", "Registered"),
    ("Attended", "Attended"),
    ("No-Show", "No-Show"),
    ("Cancelled", "Cancelled"),
]

class HistoryFilterForm(forms.Form):
    volunteer = forms.CharField(required=False)  # we'll compare id as string
    status = forms.ChoiceField(choices=HISTORY_STATUS_CHOICES, required=False)
    from_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],  # matches <input type="date">
        widget=forms.DateInput(attrs={"type": "date"})
    )

    def clean_volunteer(self):
        v = (self.cleaned_data.get("volunteer") or "").strip()
        # normalize empty -> ''
        return v
URGENCY_CHOICES = [(u.value, u.value) for u in Urgency]
PARTICIPATION_STATUS_CHOICES = [(s.value, s.value) for s in ParticipationStatus]

class ParticipationForm(forms.Form):
    id               = forms.IntegerField(required=False, min_value=1)
    volunteer_id     = forms.IntegerField(min_value=1)
    event_name       = forms.CharField(max_length=MAX_LEN_SHORT)
    description      = forms.CharField(max_length=MAX_LEN_LONG, widget=forms.Textarea)
    location         = forms.CharField(max_length=MAX_LEN_SHORT)
    required_skills  = forms.MultipleChoiceField(choices=[], required=True)  # choices set in __init__
    urgency          = forms.ChoiceField(choices=URGENCY_CHOICES)
    event_date       = forms.DateField(input_formats=["%Y-%m-%d"])
    capacity_current = forms.IntegerField(min_value=0)
    capacity_total   = forms.IntegerField(min_value=1)
    languages        = forms.MultipleChoiceField(choices=[], required=True)  # choices set in __init__
    status           = forms.ChoiceField(choices=PARTICIPATION_STATUS_CHOICES)

    def __init__(self, *args, skills=None, languages=None, **kwargs):
        super().__init__(*args, **kwargs)
        if skills:
            self.fields["required_skills"].choices = [(s, s) for s in skills]
        if languages:
            self.fields["languages"].choices = [(l, l) for l in languages]

    def clean(self):
        cleaned = super().clean()
        # Defensive checks
        for f in ["volunteer_id", "event_name", "description", "location",
                  "required_skills", "urgency", "event_date",
                  "capacity_current", "capacity_total", "languages", "status"]:
            require(cleaned.get(f), f)
        max_len(cleaned["event_name"], MAX_LEN_SHORT, "event_name")
        max_len(cleaned["location"], MAX_LEN_SHORT, "location")
        max_len(cleaned["description"], MAX_LEN_LONG, "description")
        non_negative_int(cleaned["capacity_current"], "capacity_current")
        positive_int(cleaned["capacity_total"], "capacity_total")
        list_of_strings(cleaned["required_skills"], "required_skills")
        list_of_strings(cleaned["languages"], "languages")
        capacity_ok(cleaned["capacity_current"], cleaned["capacity_total"])
        return cleaned
