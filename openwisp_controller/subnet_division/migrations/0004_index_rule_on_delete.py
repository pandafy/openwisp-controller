# Generated by Django 3.1.13 on 2021-09-27 19:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('subnet_division', '0003_related_field_allow_blank'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subnetdivisionindex',
            name='rule',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.SUBNET_DIVISION_SUBNETDIVISIONRULE_MODEL,
            ),
        ),
    ]