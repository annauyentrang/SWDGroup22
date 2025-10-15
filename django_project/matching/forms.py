from django import forms

SKILL_CHOICES = ["CPR","Driving","Lifting","Spanish","FirstAid"]
LANG_CHOICES  = ["English","Spanish","Vietnamese"]
TIME_CHOICES  = ["sat_am","sat_pm","sun_am","sun_pm"]

def _as_set(cleaned, key):  # helper
    v = cleaned.get(key, [])
    return set(v if isinstance(v, (list,tuple)) else [v]) if v else set()

class VolunteerForm(forms.Form):
    id = forms.IntegerField(min_value=1)
    name = forms.CharField(max_length=80)
    skills = forms.MultipleChoiceField(choices=[(s,s) for s in SKILL_CHOICES])
    languages = forms.MultipleChoiceField(choices=[(s,s) for s in LANG_CHOICES])
    availability = forms.MultipleChoiceField(choices=[(s,s) for s in TIME_CHOICES])
    radius_miles = forms.IntegerField(min_value=0, max_value=100)
    certifications = forms.MultipleChoiceField(choices=[("CPR","CPR")], required=False)
    constraints = forms.MultipleChoiceField(choices=[("No heavy lifting","No heavy lifting")], required=False)

    def clean(self):
        c = super().clean()
        if len(c.get("name","").strip()) == 0:
            self.add_error("name","Name cannot be blank.")
        return c

class EventForm(forms.Form):
    id = forms.IntegerField(min_value=1)
    title = forms.CharField(max_length=80)
    required_skills = forms.MultipleChoiceField(choices=[(s,s) for s in SKILL_CHOICES])
    languages = forms.MultipleChoiceField(choices=[(s,s) for s in LANG_CHOICES])
    slots = forms.IntegerField(min_value=1, max_value=500)
    time_blocks = forms.MultipleChoiceField(choices=[(s,s) for s in TIME_CHOICES])
    max_radius_miles = forms.IntegerField(min_value=0, max_value=100)
    requires = forms.MultipleChoiceField(choices=[("CPR","CPR")], required=False)

    def clean_title(self):
        t = self.cleaned_data["title"].strip()
        if len(t) < 3:
            raise forms.ValidationError("Title too short.")
        return t
