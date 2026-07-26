from django import forms

from accounts.forms import INPUT_CLASS, StyledModelForm

from .models import GeneratedReport, ReportTemplate


class TemplateUploadForm(StyledModelForm):
    class Meta:
        model = ReportTemplate
        fields = ["name", "client_name", "file", "is_client_approved"]

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith((".pptx", ".potx")):
            raise forms.ValidationError("Upload a .pptx or .potx file.")
        return f


class GenerateReportForm(forms.Form):
    report_type = forms.ChoiceField(choices=GeneratedReport.Kind.choices)
    reference_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="DSR: that day · WSR: the week containing it · MSR: the month containing it",
    )
    template = forms.ModelChoiceField(
        queryset=ReportTemplate.objects.all(),
        required=False,
        empty_label="Built-in default template",
    )
    highlights = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "One highlight per line…"}),
        required=False,
        help_text="Manager commentary — appears on the Highlights slide.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {INPUT_CLASS}".strip()


class TicketCSVForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"accept": ".csv"}),
        help_text="CSV export of tickets (see sample for expected columns).",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs["class"] = INPUT_CLASS
