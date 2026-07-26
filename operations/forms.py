from django import forms
from django.contrib.auth.models import User

from accounts.forms import INPUT_CLASS, StyledModelForm

from .models import BatchJob, ChangeRequest


class BatchJobForm(StyledModelForm):
    class Meta:
        model = BatchJob
        fields = ["name", "category", "criticality", "schedule", "cluster", "description", "is_active"]


class ChangeRequestForm(StyledModelForm):
    runbook_already_received = forms.BooleanField(
        required=False, initial=True,
        label="Runbook was handed over with this change",
    )

    class Meta:
        model = ChangeRequest
        fields = ["cr_number", "title", "description", "engineering_contact",
                  "affected_system", "target_date", "runbook", "reviewer"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "target_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reviewer"].queryset = User.objects.filter(is_active=True).order_by("first_name")
        self.fields["runbook_already_received"].widget.attrs["class"] = (
            "h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
        )
        if self.instance.pk:
            self.fields.pop("runbook_already_received")


class RunCSVForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"accept": ".csv"}),
        help_text="Columns: job_name, run_date, status, remarks (see sample).",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs["class"] = INPUT_CLASS
