# Generated by Django 4.0.4 on 2022-07-04 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0005_complaint_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicalissue',
            name='emergency_outing_permission',
            field=models.CharField(choices=[('NA', '----------'), ('Allow', 'Allow'), ('Disallow', 'Disallow')], default='NA', max_length=8),
        ),
    ]