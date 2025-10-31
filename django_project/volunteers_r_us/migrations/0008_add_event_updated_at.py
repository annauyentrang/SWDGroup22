# volunteers_r_us/migrations/0008_add_event_updated_at.py
from django.db import migrations, models
from django.utils import timezone

def backfill_updated_at(apps, schema_editor):
    Event = apps.get_model("volunteers_r_us", "Event")
    # Fill existing rows so we can drop NULL later
    Event.objects.filter(updated_at__isnull=True).update(updated_at=timezone.now())

class Migration(migrations.Migration):
    dependencies = [
        ("volunteers_r_us", "0007_remove_assignment_volunteers__event_i_23c3ff_idx_and_more"),
    ]

    operations = [
        # 1) Add as nullable so SQLite can add the column without a default prompt
        migrations.AddField(
            model_name="event",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        # 2) Backfill existing rows
        migrations.RunPython(backfill_updated_at, migrations.RunPython.noop),
        # 3) Enforce non-null going forward
        migrations.AlterField(
            model_name="event",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
