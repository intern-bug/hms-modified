# Generated by Django 4.0.4 on 2022-06-28 04:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0022_rename_allotted_at_roomdetail_allotted_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='taken_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]