# Generated by Django 4.2.11 on 2024-03-10 00:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Kick_Off', '0005_alter_events_event_location_link_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='events',
            name='event_location_link',
            field=models.URLField(),
        ),
    ]