from django import forms

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
        workplaces = Workplace.objects.filter(
            user=user,
            is_active=True,
        ).order_by("name")
        self.fields["workplace"].queryset = workplaces
        self.fields["workplace"].empty_label = "Select a workplace"
        self.fields["date"].input_formats = ["%Y-%m-%d"]
        self.fields["start_time"].input_formats = ["%H:%M"]
        self.fields["end_time"].input_formats = ["%H:%M"]
