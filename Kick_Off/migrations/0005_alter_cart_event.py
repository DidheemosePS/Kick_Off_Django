# Generated by Django 4.2.11 on 2024-03-15 20:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Kick_Off', '0004_alter_cart_event_alter_cart_participant_ticket'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cart_events', to='Kick_Off.event'),
        ),
    ]