from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('volunteers_r_us', '0002_skill_event_volunteerprofile_match'),
    ]

    operations = [
        migrations.CreateModel(
            name='VolunteerParticipation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volunteer_name', models.CharField(max_length=100)),
                ('event_name', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, default='—')),
                ('location', models.CharField(max_length=160)),
                ('required_skills', models.CharField(help_text='Comma-separated (e.g., Cooking,Organization)', max_length=160)),
                ('urgency', models.CharField(choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')], max_length=6)),
                ('event_date', models.DateField()),
                ('capacity_current', models.PositiveIntegerField(default=0)),
                ('capacity_total', models.PositiveIntegerField()),
                ('languages', models.CharField(help_text='Comma-separated (e.g., English,Spanish)', max_length=160)),
                ('status', models.CharField(choices=[('Registered', 'Registered'), ('Attended', 'Attended'), ('No-Show', 'No-Show'), ('Cancelled', 'Cancelled')], max_length=10)),
            ],
            options={
                'db_table': 'volunteer_participation',
                'ordering': ['event_date', 'volunteer_name'],
            },
        ),
    ]