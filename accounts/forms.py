from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from .models import Profile


def _mark_invalid(form):
    if not form.is_bound:
        return
    for name, field in form.fields.items():
        if form.errors.get(name):
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} border-red-400".strip()
            field.widget.attrs["aria-invalid"] = "true"


class PreferencesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "display_name",
            "currency",
            "date_format",
            "week_start",
            "weekly_hour_goal",
        ]
        widgets = {
            "display_name": forms.TextInput(
                attrs={"placeholder": "Optional — used on CSV exports"}
            ),
            "weekly_hour_goal": forms.NumberInput(
                attrs={
                    "min": "0.5",
                    "max": "168",
                    "step": "0.5",
                    "placeholder": "20",
                }
            ),
        }
        labels = {
            "display_name": "Display name",
            "currency": "Currency",
            "date_format": "Date format",
            "week_start": "Week starts on",
            "weekly_hour_goal": "Weekly hour goal",
        }
        help_texts = {
            "display_name": "Shown at the top of exported timesheets.",
            "week_start": "Used for Home, Calendar, Statistics, and export presets.",
            "weekly_hour_goal": "Leave blank if you do not have a weekly target.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["weekly_hour_goal"].required = False
        _mark_invalid(self)


class AccountPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.pop("autofocus", None)
        _mark_invalid(self)
