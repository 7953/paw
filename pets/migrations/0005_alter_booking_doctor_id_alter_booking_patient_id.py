# Generated by Django 4.1.5 on 2023-02-14 16:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pets', '0004_booking_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='Doctor_ID',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='doctors.doctorprofile'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='Patient_ID',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
