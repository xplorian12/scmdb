from django.shortcuts import render

import csv
from io import TextIOWrapper
from django.shortcuts import render
from django.db import transaction
from django.contrib import messages

from .forms import RosterUploadForm
from .models import Student, Roster


def _resolve_email_index(header_row, email_column_value):
    """
    Return zero-based index for the email column.
    If user typed a number -> treat as 1-based index.
    Otherwise match header name case-insensitively (stripped).
    """
    if email_column_value.strip().isdigit():
        idx = int(email_column_value.strip()) - 1
        if idx < 0 or idx >= len(header_row):
            raise ValueError("Email column number is out of range.")
        return idx

    wanted = email_column_value.strip().lower()
    normalized_headers = [h.strip().lower() for h in header_row]
    if wanted in normalized_headers:
        return normalized_headers.index(wanted)

    # fallback: try common names
    common = ["email", "e-mail", "email address", "mail"]
    for c in common:
        if c in normalized_headers:
            return normalized_headers.index(c)

    raise ValueError(f"Could not find email column named '{email_column_value}'. "
                     f"Available headers: {', '.join(header_row)}")


@transaction.atomic
def roster_upload_view(request):
    """
    One-page CSV processor:
    - drag/drop CSV
    - choose professor, roster name
    - specify email column (name or 1-based index)
    - specify extra rows to skip (header is always skipped)
    - creates/gets Student per email under that Professor
    - creates a Roster and attaches students (M2M)
    - shows a copy-to-clipboard box with comma+space emails
    """
    context = {"emails": None, "created_count": 0, "linked_count": 0, "roster": None}

    if request.method == "POST":
        form = RosterUploadForm(request.POST, request.FILES)
        if form.is_valid():
            professor = form.cleaned_data["professor"]
            roster_name = form.cleaned_data["roster_name"].strip()
            skip_rows = form.cleaned_data["skip_rows"]
            email_col = form.cleaned_data["email_column"]
            upload = form.cleaned_data["csv_file"]

            # Read CSV (assume UTF-8 with BOM tolerance)
            wrapper = TextIOWrapper(upload.file, encoding="utf-8-sig", newline="")
            reader = csv.reader(wrapper)

            try:
                header = next(reader)  # header row
            except StopIteration:
                messages.error(request, "The CSV file appears to be empty.")
                return render(request, "campus/roster_upload.html", {"form": form, **context})

            try:
                email_idx = _resolve_email_index(header, email_col)
            except ValueError as e:
                messages.error(request, str(e))
                return render(request, "campus/roster_upload.html", {"form": form, **context})

            # Skip extra rows (beyond header)
            for _ in range(skip_rows):
                try:
                    next(reader)
                except StopIteration:
                    break

            emails = []
            created_count = 0
            linked_count = 0

            # Create/get the roster
            roster, _created = Roster.objects.get_or_create(
                professor=professor, name=roster_name,
                defaults={"source_filename": getattr(upload, "name", "")}
            )
            if not _created:
                # existing roster: we won't delete anything, just add/merge
                pass

            for row in reader:
                if not row:
                    continue
                # Defensive: pad short rows
                if email_idx >= len(row):
                    continue
                raw = (row[email_idx] or "").strip()
                if not raw:
                    continue
                email = raw.lower()

                emails.append(email)

                # Upsert a Student under this professor by email
                student, created = Student.objects.get_or_create(
                    professor=professor,
                    email=email,
                    defaults={"first_name": "", "last_name": ""}
                )
                if created:
                    created_count += 1

                # Link to roster (M2M)
                if not roster.students.filter(pk=student.pk).exists():
                    roster.students.add(student)
                    linked_count += 1

            context.update({
                "emails": ", ".join(emails),
                "created_count": created_count,
                "linked_count": linked_count,
                "roster": roster,
            })
            messages.success(request, f"Processed {len(emails)} emails. "
                                      f"New students: {created_count}. Linked to roster: {linked_count}.")
        else:
            # form invalid – fall through to render
            pass
    else:
        form = RosterUploadForm()

    context["form"] = form
    return render(request, "campus/roster_upload.html", context)

