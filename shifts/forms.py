from datetime import date, datetime

from django import forms
from django.db.models import Q

from workspaces.models import Workplace

from .models import Shift


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = [
            "workplace",
            "date",
            "start_time",
            "end_time",
            "break_minutes",
            "notes",
        ]
        widgets = {
            "date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
            "start_time": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
            "end_time": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
            "break_minutes": forms.NumberInput(attrs={"min": "0", "step": "1"}),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional notes",
                }
            ),
        }
        labels = {
            "break_minutes": "Break (minutes)",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        workplaces = Workplace.objects.filter(user=user).filter(is_active=True)
        if self.instance and self.instance.pk:
            workplaces = Workplace.objects.filter(user=user).filter(
                Q(is_active=True) | Q(pk=self.instance.workplace_id)
            )
        workplaces = workplaces.order_by("name")
        self.fields["workplace"].queryset = workplaces
        self.fields["workplace"].empty_label = "Select a workplace"
        self.fields["date"].input_formats = ["%Y-%m-%d"]
        self.fields["start_time"].input_formats = ["%H:%M"]
        self.fields["end_time"].input_formats = ["%H:%M"]

        if self.is_bound:
            for name, field in self.fields.items():
                if self.errors.get(name):
                    existing = field.widget.attrs.get("class", "")
                    field.widget.attrs["class"] = f"{existing} border-red-400".strip()
                    field.widget.attrs["aria-invalid"] = "true"

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        break_minutes = cleaned_data.get("break_minutes") or 0

        if start_time and end_time:
            if start_time == end_time:
                self.add_error(
                    "end_time",
                    "End time must be later than start time. They cannot be the same.",
                )
            elif end_time < start_time:
                self.add_error(
                    "end_time",
                    "End time must be after start time. If the shift went past midnight, split it into two shifts.",
                )
            elif break_minutes:
                start_dt = datetime.combine(date.today(), start_time)
                end_dt = datetime.combine(date.today(), end_time)
                duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

                if break_minutes >= duration_minutes:
                    self.add_error(
                        "break_minutes",
                        f"Break ({break_minutes} min) cannot be as long as or longer than the shift ({duration_minutes} min).",
                    )

        return cleaned_data


class ShiftExportForm(forms.Form):
    workplace = forms.ModelChoiceField(
        queryset=Workplace.objects.none(),
        required=False,
        empty_label="All workplaces",
    )
    date_from = forms.DateField(
        required=False,
        label="From",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )
    date_to = forms.DateField(
        required=False,
        label="To",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        workplaces = Workplace.objects.filter(user=user).order_by("name")
        self.fields["workplace"].queryset = workplaces

        if self.is_bound:
            for name, field in self.fields.items():
                if self.errors.get(name):
                    existing = field.widget.attrs.get("class", "")
                    field.widget.attrs["class"] = f"{existing} border-red-400".strip()
                    field.widget.attrs["aria-invalid"] = "true"

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")
        if date_from and date_to and date_from > date_to:
            self.add_error("date_to", "End date must be on or after the start date.")
        return cleaned_data
