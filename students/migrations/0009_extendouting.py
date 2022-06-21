# Generated by Django 4.0.4 on 2022-06-13 06:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0008_alter_outing_permission_delete_extendouting'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtendOuting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fromDate', models.DateTimeField()),
                ('toDate', models.DateTimeField()),
                ('remark_by_caretaker', models.CharField(max_length=255, null=True)),
                ('remark_by_warden', models.CharField(max_length=255, null=True)),
                ('purpose', models.CharField(max_length=255)),
                ('parent_consent', models.CharField(choices=[('Accepted', 'Accepted'), ('Denied', 'Denied')], default='NA', max_length=8)),
                ('permission', models.CharField(choices=[('Pending', 'Pending'), ('Processing', 'Processing'), ('Granted', 'Granted'), ('Rejected', 'Rejected'), ('Revoked', 'Revoked'), ('Pending Extension', 'Pending Extension'), ('Processing Extension', 'Processing Extension'), ('Extension Granted', 'Extension Granted'), ('Extension Rejected', 'Extension Rejected')], default='Pending', max_length=20)),
                ('place_of_visit', models.CharField(max_length=255)),
                ('outing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='students.outing')),
            ],
            options={
                'managed': True,
            },
        ),
    ]