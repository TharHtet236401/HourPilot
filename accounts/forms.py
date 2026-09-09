from allauth.account.models import EmailAddress
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

from .models import Profile

User = get_user_model()


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


class EmailChangeForm(forms.Form):
    email = forms.EmailField(
        label="New email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Current password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        _mark_invalid(self)

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if email.lower() == (self.user.email or "").lower():
            raise forms.ValidationError("That is already your email.")
        taken = (
            User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists()
            or EmailAddress.objects.filter(email__iexact=email)
            .exclude(user=self.user)
            .exists()
        )
        if taken:
            raise forms.ValidationError("That email is already in use.")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("That password is not correct.")
        return password


class AccountPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.pop("autofocus", None)
        _mark_invalid(self)
