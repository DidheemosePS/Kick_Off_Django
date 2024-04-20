# Generated by Django 4.2.11 on 2024-03-21 18:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Kick_Off', '0005_alter_cart_event'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('participant_name', models.CharField(max_length=100)),
                ('event_rating', models.TextField()),
                ('event_star', models.IntegerField()),
                ('event_ticket_id', models.IntegerField()),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rating_events', to='Kick_Off.event')),
                ('participant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rating_participants', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
