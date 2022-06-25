# Generated by Django 4.0.4 on 2022-06-21 06:35

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0016_outing_mess_rebate_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='roomdetail',
            name='allotted_at',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Vacation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vacated_on', models.DateField()),
                ('mode_of_journey', models.CharField(max_length=255)),
                ('journey_destination', models.CharField(max_length=255)),
                ('iron_cot_status', models.CharField(choices=[('Functioning', 'Functioning'), ('Defective', 'Defective')], max_length=11)),
                ('tube_light_status', models.CharField(choices=[('Functioning', 'Functioning'), ('Defective', 'Defective')], max_length=11)),
                ('fan_status', models.CharField(choices=[('Functioning', 'Functioning'), ('Defective', 'Defective')], max_length=11)),
                ('fan_regulator_status', models.CharField(choices=[('Functioning', 'Functioning'), ('Defective', 'Defective')], max_length=11)),
                ('cupboards_status', models.CharField(choices=[('Functioning', 'Functioning'), ('Defective', 'Defective')], max_length=11)),
                ('switches_status', models.CharField(choices=[('Functioning', 'Functioning'), ('Defective', 'Defective')], max_length=11)),
                ('amperes_socket_15_status', models.CharField(choices=[('Functioning', 'Functioning'), ('Defective', 'Defective')], max_length=11)),
                ('iron_cot_remarks', models.CharField(blank=True, max_length=255, null=True)),
                ('tube_light_remarks', models.CharField(blank=True, max_length=255, null=True)),
                ('fan_remarks', models.CharField(blank=True, max_length=255, null=True)),
                ('fan_regulator_remarks', models.CharField(blank=True, max_length=255, null=True)),
                ('cupboards_remarks', models.CharField(blank=True, max_length=255, null=True)),
                ('switches_remarks', models.CharField(blank=True, max_length=255, null=True)),
                ('amperes_socket_15_remarks', models.CharField(blank=True, max_length=255, null=True)),
                ('room_detail', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='students.roomdetail')),
            ],
        ),
    ]