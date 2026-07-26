from django import forms

from accounts.forms import INPUT_CLASS, StyledModelForm

from .models import BatchJob


class BatchJobForm(StyledModelForm):
    class Meta:
        model = BatchJob
        fields = ["name", "category", "criticality", "schedule", "cluster", "description", "is_active"]


class RunCSVForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"accept": ".csv"}),
        help_text="Columns: job_name, run_date, status, remarks (see sample).",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs["class"] = INPUT_CLASS
