# Generated migration for adding status tracking fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reversal_zones', '0002_auto_20260524_1200'),  # Update this to match your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='reversalzone',
            name='status',
            field=models.CharField(
                max_length=20,
                default='OPEN',
                choices=[
                    ('OPEN', 'Open'),
                    ('TARGET_HIT', 'Target Hit'),
                    ('SL_HIT', 'Stop Loss Hit'),
                ]
            ),
        ),
        migrations.AddField(
            model_name='reversalzone',
            name='status_updated_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
