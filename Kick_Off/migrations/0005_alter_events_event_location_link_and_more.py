# Generated by Django 4.2.11 on 2024-03-10 00:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Kick_Off', '0004_alter_events_event_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='events',
            name='event_location_link',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='events',
            name='event_time',
            field=models.TimeField(),
        ),
    ]