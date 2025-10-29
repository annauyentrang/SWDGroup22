import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('volunteers_r_us', '0003_volunteerparticipation'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=50)),
                ('address1', models.CharField(max_length=100)),
                ('address2', models.CharField(blank=True, max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=2)),
                ('zipcode', models.CharField(max_length=10)),
                ('skills', models.JSONField(default=list)),
                ('preferences', models.TextField(blank=True)),
                ('availability', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]