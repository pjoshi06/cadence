from django import forms
from django.contrib.auth.models import User

from .models import Profile

INPUT_CLASS = (
    "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 "
    "placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 "
    "focus:ring-indigo-200 bg-white"
)


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = INPUT_CLASS
            if isinstance(field.widget, forms.CheckboxInput):
                css = "h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css}".strip()


class MemberForm(StyledModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField()
    username = forms.CharField(max_length=150)
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank to keep unchanged (existing members).",
    )

    class Meta:
        model = Profile
        fields = [
            "role", "designation", "sn_user_id", "assignment_group",
            "skills", "phone", "annual_leave_balance",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("first_name", "last_name", "email", "username", "password"):
            self.fields[name].widget.attrs["class"] = INPUT_CLASS
        if self.instance.pk:
            user = self.instance.user
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email
            self.fields["username"].initial = user.username
            self.fields["username"].disabled = True

    def clean_username(self):
        username = self.cleaned_data["username"]
        if not self.instance.pk and User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.pk:
            user = profile.user
        else:
            user = User(username=self.cleaned_data["username"])
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if self.cleaned_data["password"]:
            user.set_password(self.cleaned_data["password"])
        user.save()
        profile.user = user
        if commit:
            profile.save()
        return profile
