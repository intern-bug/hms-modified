# Generated by Django 4.0.4 on 2022-06-28 04:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0023_attendance_taken_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendance',
            name='taken_at',
        ),
    ]
