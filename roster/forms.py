from django import forms

from accounts.forms import StyledModelForm

from .models import SHIFT_COLORS, Shift

COLOR_LABELS = {
    "sky": "Sky blue",
    "indigo": "Indigo",
    "violet": "Violet",
    "emerald": "Green",
    "amber": "Amber",
    "slate": "Grey",
}


class ShiftForm(StyledModelForm):
    class Meta:
        model = Shift
        fields = ["code", "name", "start_time", "end_time", "color", "is_active"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "end_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["color"].choices = [
            (key, COLOR_LABELS.get(key, key)) for key in SHIFT_COLORS
        ]
        self.fields["code"].widget.attrs["placeholder"] = "e.g. S1"
        self.fields["name"].widget.attrs["placeholder"] = "e.g. Morning"

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        qs = Shift.objects.filter(code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A shift with this code already exists.")
        return code
