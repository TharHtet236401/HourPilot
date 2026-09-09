from django import forms

from .models import Workplace


class WorkplaceForm(forms.ModelForm):
    class Meta:
        model = Workplace
        fields = ["name", "hourly_rate", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Tesco, cafe, warehouse..."}),
            "hourly_rate": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "12.50",
                }
            ),
        }
        labels = {
            "hourly_rate": "Hourly rate",
            "is_active": "Active workplace",
        }

    def __init__(self, *args, currency_symbol="£", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hourly_rate"].label = f"Hourly rate ({currency_symbol})"
        if not self.instance.pk:
            self.fields.pop("is_active")

        if self.is_bound:
            for name, field in self.fields.items():
                if self.errors.get(name):
                    existing = field.widget.attrs.get("class", "")
                    field.widget.attrs["class"] = f"{existing} border-red-400".strip()
                    field.widget.attrs["aria-invalid"] = "true"
