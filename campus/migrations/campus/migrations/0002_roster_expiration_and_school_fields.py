# campus/migrations/0002_roster_expiration_and_school_fields.py
from django.db import migrations, models
from datetime import timedelta
from django.utils import timezone
import campus.models  # to reference default_roster_expiration

def backfill_roster_expiration(apps, schema_editor):
    Roster = apps.get_model('campus', 'Roster')
    for r in Roster.objects.all():
        base = r.created_at.date() if r.created_at else timezone.now().date()
        r.expiration_date = base + timedelta(days=90)
        r.save(update_fields=['expiration_date'])

class Migration(migrations.Migration):
    # ⬇️ IMPORTANT: replace '0001_initial' with your LAST migration filename in campus/migrations (without .py)
    dependencies = [
        ('campus', '0001_initial'),
    ]

    operations = [
        # School fields
        migrations.AddField(
            model_name='school',
            name='country',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='school',
            name='purchased_accounts',
            field=models.PositiveIntegerField(default=0, help_text='Purchased account allotment for this school.'),
        ),

        # Roster expiration (add nullable first so we can backfill)
        migrations.AddField(
            model_name='roster',
            name='expiration_date',
            field=models.DateField(null=True, blank=True),
        ),

        # Backfill existing rows using created_at + 90 days
        migrations.RunPython(backfill_roster_expiration, migrations.RunPython.noop),

        # Make it non-null going forward and set the real default (+90 days)
        migrations.AlterField(
            model_name='roster',
            name='expiration_date',
            field=models.DateField(default=campus.models.default_roster_expiration),
        ),
    ]
