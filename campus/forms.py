from django import forms
from .models import Professor
from .models import Roster
from django.core.exceptions import ValidationError


class RosterForm(forms.ModelForm):
    # Optional CSV addon (drag & drop onto this file input works in browsers)
    csv_file     = forms.FileField(required=False, help_text="Optional: Drag & drop a .csv to add emails")
    email_column = forms.CharField(required=False, help_text="Header name OR 1-based column number")
    skip_rows    = forms.IntegerField(required=False, min_value=0, initial=0,
                                      help_text="Extra rows to skip after header (header is auto-skipped)")

    class Meta:
        model  = Roster
        fields = ['professor', 'name', 'notes', 'discount_amount', 'invoice_sent', 'students']
        widgets = {'notes': forms.Textarea(attrs={'rows': 3})}

    def clean(self):
        cleaned = super().clean()
        upload = cleaned.get('csv_file')
        email_col = (cleaned.get('email_column') or '').strip()
        if upload and not email_col:
            raise ValidationError("Please provide the email column (name or number) for the CSV.")
        return cleaned



from django import forms
from .models import Professor, Roster
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
import re


class QuickAddEmailsForm(forms.Form):
    professor = forms.ModelChoiceField(
        queryset=Professor.objects.select_related("school"),
        help_text="Who owns these student(s)?"
    )
    roster = forms.ModelChoiceField(
        queryset=Roster.objects.select_related("professor"),
        required=False,
        help_text="Optional: add all to this roster"
    )
    emails = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "Paste one or many emails…"}),
        help_text="Separate with comma, space, semicolon, or newline."
    )

    def clean(self):
        cleaned = super().clean()
        prof = cleaned.get("professor")
        rost = cleaned.get("roster")
        if rost and rost.professor_id != prof.id:
            self.add_error("roster", "Selected roster belongs to a different professor.")

        raw = cleaned.get("emails", "") or ""
        parts = [p.strip().lower() for p in re.split(r"[,\s;]+", raw) if p.strip()]
        if not parts:
            raise ValidationError("Please provide at least one email address.")

        validator = EmailValidator()
        valid, invalid = [], []
        for p in parts:
            try:
                validator(p)
                valid.append(p)
            except ValidationError:
                invalid.append(p)

        if not valid:
            raise ValidationError("No valid email addresses found.")

        cleaned["emails_list"] = list(dict.fromkeys(valid))  # de-dupe, keep order
        cleaned["invalid_list"] = invalid
        return cleaned
