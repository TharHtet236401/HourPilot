from django import forms

from .models import Workplace


class WorkplaceForm(forms.ModelForm):
    class Meta:
        model = Workplace
        fields = ["name", "hourly_rate"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Tesco, cafe, warehouse..."}
            ),
            "hourly_rate": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "12.50",
                }
            ),
        }
        labels = {
            "hourly_rate": "Hourly rate (£)",
        }
