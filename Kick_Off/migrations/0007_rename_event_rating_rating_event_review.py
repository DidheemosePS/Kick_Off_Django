# Generated by Django 4.2.11 on 2024-03-21 19:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Kick_Off', '0006_rating'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rating',
            old_name='event_rating',
            new_name='event_review',
        ),
    ]
