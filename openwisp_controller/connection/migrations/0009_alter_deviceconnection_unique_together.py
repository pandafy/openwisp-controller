# Generated by Django 3.2.20 on 2023-08-24 12:35

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.CONFIG_DEVICE_MODEL),
        ('connection', '0008_remove_conflicting_deviceconnections'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='deviceconnection',
            unique_together={('device', 'credentials')},
        ),
    ]
