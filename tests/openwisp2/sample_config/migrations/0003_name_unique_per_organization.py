# Generated by Django 3.1.6 on 2021-02-11 22:50

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sample_config', '0002_default_groups_permissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='template',
            name='name',
            field=models.CharField(db_index=True, max_length=64),
        ),
        migrations.AlterField(
            model_name='vpn',
            name='name',
            field=models.CharField(db_index=True, max_length=64),
        ),
        migrations.AlterUniqueTogether(
            name='vpn', unique_together={('organization', 'name')}
        ),
        migrations.AddField(
            model_name='vpn',
            name='subnet',
            field=models.ForeignKey(
                blank=True,
                help_text='Subnet IP addresses used by VPN clients, if applicable',
                null=True,
                on_delete=models.deletion.SET_NULL,
                to=settings.OPENWISP_IPAM_SUBNET_MODEL,
                verbose_name='Subnet',
            ),
        ),
    ]